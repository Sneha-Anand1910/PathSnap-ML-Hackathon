"""HMM/Viterbi decoder for candidate road arcs."""
from __future__ import annotations
from dataclasses import dataclass
from heapq import heappop, heappush
from math import inf, log
from typing import Mapping, Sequence

from src.features.road_network import RoadNetwork


@dataclass(frozen=True)
class DecodeResult:
    predicted_arc_ids: list[int | None]
    log_score: float
    decoded_observations: int
    empty_candidate_observations: list[int]
    disconnected_transition_count: int


class RoadTransitionGraph:
    """Directed road graph with bounded-hop shortest connectors and memoization."""
    def __init__(self, network: RoadNetwork, max_hops: int = 4) -> None:
        if max_hops < 1:
            raise ValueError("max_hops must be at least one.")
        self.max_hops = max_hops
        self.adjacency = {}
        for segment in network.segments:
            self.adjacency.setdefault(segment.from_node_id, []).append(
                (segment.to_node_id, segment.length_m)
            )
        self._cache = {}

    def connector(self, start_node: int, end_node: int):
        """Shortest directed path of at most max_hops arcs between two nodes."""
        key = (start_node, end_node)
        if key in self._cache:
            return self._cache[key]
        if start_node == end_node:
            self._cache[key] = (0.0, 0)
            return self._cache[key]
        queue = [(0.0, 0, start_node)]
        best = {(start_node, 0): 0.0}
        answer = None
        while queue:
            distance, hops, node = heappop(queue)
            if distance != best.get((node, hops)):
                continue
            if node == end_node:
                answer = (distance, hops)
                break
            if hops == self.max_hops:
                continue
            for next_node, edge_length in self.adjacency.get(node, ()):
                key2 = (next_node, hops + 1)
                next_distance = distance + edge_length
                if next_distance < best.get(key2, inf):
                    best[key2] = next_distance
                    heappush(queue, (next_distance, hops + 1, next_node))
        self._cache[key] = answer
        return answer


def _arc_id(state: Mapping) -> int:
    return int(state.get("candidate_arc_id", state.get("arc_id")))


def _probabilities(states: Sequence[Mapping]) -> list[float]:
    scores = [max(0.0, float(s.get("probability", s.get("model_probability", s.get("score", 0.0)))))
              for s in states]
    total = sum(scores)
    return [score / total for score in scores] if total > 0 else [1.0 / len(states)] * len(states)


def _transition_distance(previous: Mapping, current: Mapping, graph: RoadTransitionGraph):
    previous_arc, current_arc = _arc_id(previous), _arc_id(current)
    previous_fraction = float(previous.get("along_arc_fraction", 0.5))
    current_fraction = float(current.get("along_arc_fraction", 0.5))
    previous_length, current_length = float(previous["road_length_m"]), float(current["road_length_m"])
    if previous_arc == current_arc:
        delta = (current_fraction - previous_fraction) * previous_length
        return (max(0.0, delta), 0) if delta >= 0 else (abs(delta), 0)

    connector = graph.connector(int(previous["to_node_id"]), int(current["from_node_id"]))
    if connector is None:
        return None
    connector_distance, connector_hops = connector
    distance = max(0.0, (1.0 - previous_fraction) * previous_length)
    distance += connector_distance + max(0.0, current_fraction * current_length)
    return distance, connector_hops


def _decode_segment(observations, network, graph, observed_distances_m, beta_m, disconnected_penalty):
    emissions = []
    for states in observations:
        emissions.append([log(max(p, 1e-12)) for p in _probabilities(states)])
    score_rows = [emissions[0]]
    back_rows = [[None] * len(observations[0])]
    disconnected_count = 0

    for t in range(1, len(observations)):
        prior_states, current_states = observations[t - 1], observations[t]
        observed = None if observed_distances_m is None else observed_distances_m[t - 1]
        current_scores = [-inf] * len(current_states)
        current_back = [None] * len(current_states)
        for j, current in enumerate(current_states):
            for i, previous in enumerate(prior_states):
                transition = _transition_distance(previous, current, graph)
                if transition is None:
                    continue
                route_distance, _ = transition
                transition_score = 0.0 if observed is None else -abs(route_distance - observed) / beta_m
                score = score_rows[-1][i] + transition_score + emissions[t][j]
                if score > current_scores[j]:
                    current_scores[j], current_back[j] = score, i
        if not any(index is not None for index in current_back):
            # Restart with a penalty when every transition is disconnected.
            best_prior = max(range(len(prior_states)), key=lambda i: score_rows[-1][i])
            current_scores = [score_rows[-1][best_prior] + value - disconnected_penalty
                              for value in emissions[t]]
            current_back = [best_prior] * len(current_states)
            disconnected_count += 1
        score_rows.append(current_scores)
        back_rows.append(current_back)

    state = max(range(len(score_rows[-1])), key=lambda i: score_rows[-1][i])
    path = [state]
    for t in range(len(observations) - 1, 0, -1):
        prior = back_rows[t][path[-1]]
        path.append(0 if prior is None else prior)
    path.reverse()
    decoded = [_arc_id(observations[t][index]) for t, index in enumerate(path)]
    return decoded, max(score_rows[-1]), disconnected_count


def viterbi_decode(candidate_sequences, network: RoadNetwork, *,
                   observed_distances_m=None, max_connector_hops=4,
                   beta_m=50.0, disconnected_penalty=20.0) -> DecodeResult:
    """Decode a coherent arc sequence from per-observation model scores.

    Each candidate mapping needs arc ID, probability/score, endpoint node IDs,
    road_length_m and optionally along_arc_fraction. Empty lists yield None and
    split decoding into independent segments.
    """
    if beta_m <= 0 or disconnected_penalty <= 0:
        raise ValueError("beta_m and disconnected_penalty must be positive.")
    if observed_distances_m is not None and len(observed_distances_m) != max(0, len(candidate_sequences) - 1):
        raise ValueError("observed_distances_m must have one value between adjacent observations.")
    graph = RoadTransitionGraph(network, max_connector_hops)
    predictions = [None] * len(candidate_sequences)
    empty = [i for i, states in enumerate(candidate_sequences) if not states]
    disconnected_total = 0
    total_score = 0.0
    start = 0
    while start < len(candidate_sequences):
        while start < len(candidate_sequences) and not candidate_sequences[start]:
            start += 1
        if start >= len(candidate_sequences):
            break
        end = start
        while end < len(candidate_sequences) and candidate_sequences[end]:
            end += 1
        segment = candidate_sequences[start:end]
        distances = None if observed_distances_m is None else observed_distances_m[start:end - 1]
        decoded, score, disconnected = _decode_segment(
            segment, network, graph, distances, beta_m, disconnected_penalty
        )
        predictions[start:end] = decoded
        total_score += score
        disconnected_total += disconnected
        start = end
    return DecodeResult(
        predicted_arc_ids=predictions,
        log_score=total_score,
        decoded_observations=len(candidate_sequences) - len(empty),
        empty_candidate_observations=empty,
        disconnected_transition_count=disconnected_total,
    )

def group_candidate_rows(candidate_rows, model_probabilities, observation_count: int):
    """Attach positive-class model probabilities and group candidates by observation."""
    if observation_count < 0:
        raise ValueError("observation_count cannot be negative.")
    if len(candidate_rows) != len(model_probabilities):
        raise ValueError("One positive-class probability is required per candidate row.")
    grouped = [[] for _ in range(observation_count)]
    required = ("candidate_arc_id", "from_node_id", "to_node_id",
                "road_length_m", "along_arc_fraction")
    for row, probability in zip(candidate_rows, model_probabilities):
        observation_idx = int(row["observation_idx"])
        if not 0 <= observation_idx < observation_count:
            raise ValueError(f"Observation index {observation_idx} is outside the requested sequence.")
        candidate = {key: row[key] for key in required}
        candidate["probability"] = float(probability)
        grouped[observation_idx].append(candidate)
    for states in grouped:
        states.sort(key=lambda item: item["candidate_arc_id"])
    return grouped


def gps_step_distances(projected_points):
    """Return metric GPS displacement for every pair of consecutive observations."""
    from math import hypot
    return [
        hypot(current[0] - previous[0], current[1] - previous[1])
        for previous, current in zip(projected_points, projected_points[1:])
    ]
