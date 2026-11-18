"""Candidate-level data construction and candidate-recall reporting."""
from math import inf
from .candidate_generation import SegmentGrid, generate_candidates
from .feature_engineering import GPSObservation, engineer_candidate_features, extract_gps_features
from .road_network import build_road_network, point_to_segment_distance

def _rows(value):
    if hasattr(value, "itertuples"):
        return list(value.itertuples(index=False, name=None))
    if hasattr(value, "tolist"):
        value = value.tolist()
    values = list(value)
    if not values:
        return []
    if not isinstance(values[0], (list, tuple)):
        return [(item,) for item in values]
    return [tuple(row) for row in values]

def align_reference_route(points_xy, route_arc_ids, network, *, advance_penalty_m=1.0,
                          search_radius_m=500.0, beam_width=24):
    """Spatially pruned dynamic alignment; route position may stay or advance, never retreat."""
    if not route_arc_ids:
        raise ValueError("The reference route is empty.")
    if advance_penalty_m < 0 or search_radius_m <= 0 or beam_width <= 0:
        raise ValueError("Alignment parameters must be positive (penalty may be zero).")
    by_id = {s.arc_id: s for s in network.segments}
    route = []
    for pos, arc_id in enumerate(route_arc_ids):
        if arc_id not in by_id:
            raise ValueError(f"Unknown route arc ID {arc_id} at position {pos}.")
        route.append(by_id[arc_id])
    if not points_xy:
        return []
    grid = SegmentGrid(route)
    state_rows = []
    for point in points_xy:
        nearby = grid.query(point, search_radius_m)
        scored = [(point_to_segment_distance(point, route[i].start_xy, route[i].end_xy), i)
                  for i in nearby]
        scored = [item for item in scored if item[0] <= search_radius_m]
        if not scored:
            # Rare outlier fallback: scan route once for this observation.
            scored = [(point_to_segment_distance(point, s.start_xy, s.end_xy), i)
                      for i, s in enumerate(route)]
        scored.sort()
        state_rows.append(sorted((i, d) for d, i in scored[:beam_width]))

    costs = {i: distance + i * advance_penalty_m for i, distance in state_rows[0]}
    back_rows = []
    for t in range(1, len(state_rows)):
        current, back = {}, {}
        for position, distance in state_rows[t]:
            options = [(cost + advance_penalty_m * (position - prior), prior)
                       for prior, cost in costs.items() if prior <= position]
            if options:
                best_cost, best_prior = min(options)
                current[position] = distance + best_cost
                back[position] = best_prior
        if not current:
            # Keep a valid monotonic path if GPS noise places all shortlisted arcs behind it.
            prior = min(costs)
            current[prior] = costs[prior] + point_to_segment_distance(
                points_xy[t], route[prior].start_xy, route[prior].end_xy)
            back[prior] = prior
        costs = current
        back_rows.append(back)

    state = min(costs, key=costs.get)
    positions = [state]
    for back in reversed(back_rows):
        state = back[state]
        positions.append(state)
    positions.reverse()
    return [route[position].arc_id for position in positions]

def build_candidate_table(trip, *, candidate_radius_m=100.0, max_candidates=None,
                          include_labels=False, advance_penalty_m=1.0):
    """Accept Member 1's dictionary unchanged: trip_id/track/nodes/arcs/route."""
    required = {"trip_id", "track", "nodes", "arcs", "route"}
    missing = required - set(trip)
    if missing:
        raise ValueError(f"Trip data is missing keys: {sorted(missing)}")
    nodes = [(float(r[0]), float(r[1])) for r in _rows(trip["nodes"])]
    arcs = [(int(r[0]), int(r[1])) for r in _rows(trip["arcs"])]
    track = [GPSObservation(float(r[0]), float(r[1]), float(r[2])) for r in _rows(trip["track"])]
    route = [int(r[0]) for r in _rows(trip["route"])]
    if include_labels and not route:
        raise ValueError("Labels requested but route is empty.")
    network = build_road_network(nodes, arcs)
    gps = extract_gps_features(track, network.projection)
    points = [(row["x_m"], row["y_m"]) for row in gps]
    aligned = (align_reference_route(points, route, network,
                advance_penalty_m=advance_penalty_m) if include_labels else None)
    grid = SegmentGrid(network.segments)
    by_id = {s.arc_id: s for s in network.segments}
    rows = []
    for i, (gps_row, point) in enumerate(zip(gps, points)):
        candidates = generate_candidates(point, network, candidate_radius_m,
                                         segment_grid=grid, max_candidates=max_candidates)
        for rank, candidate in enumerate(candidates, 1):
            row = engineer_candidate_features(gps_row, candidate, by_id[candidate.arc_id])
            row.update({"trip_id": str(trip["trip_id"]), "candidate_rank": rank,
                        "label": None if aligned is None else int(candidate.arc_id == aligned[i])})
            rows.append(row)
    return rows

def candidate_recall_report(candidate_rows, expected_arc_ids, trip_id):
    """Report observations whose expected aligned route arc is missing from candidates."""
    found = {(row["observation_idx"], row["candidate_arc_id"]) for row in candidate_rows
             if row["trip_id"] == str(trip_id)}
    missed = [i for i, arc_id in enumerate(expected_arc_ids) if (i, arc_id) not in found]
    total = len(expected_arc_ids)
    return {"trip_id": str(trip_id), "observations": total, "recalled": total-len(missed),
            "missed": len(missed), "candidate_recall": None if not total else (total-len(missed))/total,
            "missed_observation_indices": missed}
