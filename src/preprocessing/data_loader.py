from pathlib import Path
import pandas as pd


def load_trip(trip_folder):
    """
    Load GPS observations, road-network nodes,
    road-network arcs and reference routes
    for a single PathSnap trip.
    """

    trip_folder = Path(trip_folder)
    trip_id = trip_folder.name

    track_path = trip_folder / f"{trip_id}.track"
    nodes_path = trip_folder / f"{trip_id}.nodes"
    arcs_path = trip_folder / f"{trip_id}.arcs"
    route_path = trip_folder / f"{trip_id}.route"

    # GPS trajectory
    track = pd.read_csv(
        track_path,
        sep=r"\s+",
        header=None,
        names=["longitude", "latitude", "timestamp"]
    )

    # Road-network nodes
    nodes = pd.read_csv(
        nodes_path,
        sep=r"\s+",
        header=None,
        names=["longitude", "latitude"]
    )

    # Road-network arcs
    arcs = pd.read_csv(
        arcs_path,
        sep=r"\s+",
        header=None,
        names=["from_node", "to_node"]
    )

    # Arc IDs correspond to row positions
    arcs.index.name = "arc_id"

    # Reference route
    route = pd.read_csv(
        route_path,
        sep=r"\s+",
        header=None,
        names=["arc_id"]
    )

    return {
        "trip_id": trip_id,
        "track": track,
        "nodes": nodes,
        "arcs": arcs,
        "route": route
    }


if __name__ == "__main__":

    from data_validator import validate_trip

    trip_path = (
        Path.home()
        / "Downloads"
        / "Student folder"
        / "train"
        / "00000034"
    )

    trip = load_trip(trip_path)

    issues = validate_trip(trip)