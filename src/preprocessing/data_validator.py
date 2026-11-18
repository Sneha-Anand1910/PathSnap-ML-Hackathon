
import numpy as np


def validate_trip(trip):

    print("\n" + "=" * 50)
    print("DATA VALIDATION REPORT")
    print("Trip ID:", trip["trip_id"])
    print("=" * 50)

    track = trip["track"]
    nodes = trip["nodes"]
    arcs = trip["arcs"]
    route = trip["route"]

    issues = []

    # 1. Check missing values
    print("\n1. MISSING VALUES")

    for name, df in [
        ("track", track),
        ("nodes", nodes),
        ("arcs", arcs),
        ("route", route)
    ]:
        missing = int(df.isnull().sum().sum())
        print(f"{name}: {missing}")

        if missing:
            issues.append(f"{name} contains missing values")

    # 2. Check duplicate records
    print("\n2. DUPLICATE RECORDS")

    for name, df in [
        ("track", track),
        ("nodes", nodes),
        ("arcs", arcs),
        ("route", route)
    ]:
        duplicates = int(df.duplicated().sum())
        print(f"{name}: {duplicates}")

    # 3. Check GPS coordinates
    print("\n3. GPS COORDINATES")

    valid_track = (
        track["longitude"].between(-180, 180)
        & track["latitude"].between(-90, 90)
    )

    print("Invalid GPS rows:", int((~valid_track).sum()))

    if not valid_track.all():
        issues.append("Invalid GPS coordinates found")

    # 4. Check timestamps
    print("\n4. TIMESTAMP VALIDATION")

    timestamps = track["timestamp"]

    print("Chronological order:",
          timestamps.is_monotonic_increasing)

    print("Duplicate timestamps:",
          int(timestamps.duplicated().sum()))

    if not timestamps.is_monotonic_increasing:
        issues.append("Timestamps are not chronologically ordered")

    # 5. Check road-network node references
    print("\n5. ROAD NETWORK VALIDATION")

    valid_arcs = (
        arcs["from_node"].between(0, len(nodes) - 1)
        & arcs["to_node"].between(0, len(nodes) - 1)
    )

    print("Invalid arc connections:",
          int((~valid_arcs).sum()))

    if not valid_arcs.all():
        issues.append("Some arcs reference invalid node IDs")

    # 6. Check route arc IDs
    print("\n6. ROUTE VALIDATION")

    route_ids = route["arc_id"]

    valid_route_ids = (
        route_ids.notna()
        & (route_ids >= 0)
        & (route_ids < len(arcs))
        & (route_ids % 1 == 0)
    )

    print("Total route segments:", len(route))
    print("Invalid route arc IDs:",
          int((~valid_route_ids).sum()))

    if not valid_route_ids.all():
        issues.append("Some route IDs are invalid")

    # 7. Check consecutive route connectivity
    print("\n7. ROUTE CONNECTIVITY")

    connectivity_errors = 0

    if valid_route_ids.all():
        ids = route_ids.astype(int).tolist()

        for current_id, next_id in zip(ids, ids[1:]):
            current_arc = arcs.iloc[current_id]
            next_arc = arcs.iloc[next_id]

            if current_arc["to_node"] != next_arc["from_node"]:
                connectivity_errors += 1

    print("Disconnected consecutive segments:",
          connectivity_errors)

    if connectivity_errors:
        issues.append("Some consecutive route segments are disconnected")

    # Final report
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)

    if issues:
        for issue in issues:
            print("WARNING:", issue)
    else:
        print("No validation issues detected.")

    return issues
