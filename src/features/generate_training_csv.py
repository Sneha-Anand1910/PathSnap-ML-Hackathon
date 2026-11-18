"""Generate the Member 3 candidate-level training CSV for all training trips."""
from __future__ import annotations

import argparse
import csv
import io
import zipfile
from pathlib import Path

from .create_training_data import align_reference_route, build_candidate_table, candidate_recall_report
from .road_network import build_road_network

CSV_COLUMNS = [
    "trip_id", "observation_idx", "candidate_arc_id", "candidate_rank",
    "distance_m", "projection_x_m", "projection_y_m", "along_arc_fraction",
    "bearing_difference", "label", "speed_mps", "gps_heading_deg",
    "road_bearing_deg", "road_length_m", "time_gap_s", "from_node_id", "to_node_id",
]

def _parse_rows(text: str, width: int) -> list[tuple[float, ...]]:
    rows = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        values = line.split()
        if len(values) != width:
            raise ValueError(f"Expected {width} columns, got {len(values)} at line {line_number}.")
        rows.append(tuple(float(value) for value in values))
    return rows

def _trip_from_text(trip_id: str, read_text) -> dict:
    return {
        "trip_id": trip_id,
        "track": _parse_rows(read_text(f"{trip_id}.track"), 3),
        "nodes": _parse_rows(read_text(f"{trip_id}.nodes"), 2),
        "arcs": [tuple(map(int, row)) for row in _parse_rows(read_text(f"{trip_id}.arcs"), 2)],
        "route": [int(row[0]) for row in _parse_rows(read_text(f"{trip_id}.route"), 1)],
    }

def _load_directory(data_root: Path, trip_id: str) -> dict:
    folder = data_root / "train" / trip_id
    return _trip_from_text(trip_id, lambda name: (folder / name).read_text(encoding="utf-8"))

def _archive_members(archive_path: Path):
    outer = zipfile.ZipFile(archive_path)
    if "Student folder.zip" in outer.namelist():
        inner_bytes = outer.read("Student folder.zip")
        outer.close()
        inner = zipfile.ZipFile(io.BytesIO(inner_bytes))
        return inner, True
    return outer, False

def _load_archive(archive_path: Path, trip_id: str) -> dict:
    archive, nested_root = _archive_members(archive_path)
    base = "Student folder/" if nested_root else ""
    prefix = f"{base}train/{trip_id}/{trip_id}"
    try:
        return _trip_from_text(
            trip_id,
            lambda name: archive.read(prefix + name.split(trip_id, 1)[1]).decode("utf-8"),
        )
    finally:
        archive.close()

def _trip_ids_from_archive(archive_path: Path) -> list[str]:
    archive, nested_root = _archive_members(archive_path)
    base = "Student folder/" if nested_root else ""
    prefix = f"{base}train/"
    ids = sorted({
        name[len(prefix):].split("/", 1)[0]
        for name in archive.namelist()
        if name.startswith(prefix) and name.endswith(".track")
    })
    archive.close()
    return ids

def generate(data_root: Path | None, archive_path: Path | None, output_path: Path,
             candidate_radius_m: float = 100.0) -> dict:
    if (data_root is None) == (archive_path is None):
        raise ValueError("Provide exactly one of data_root or archive_path.")
    if archive_path is not None:
        trip_ids = _trip_ids_from_archive(archive_path)
        loader = lambda trip_id: _load_archive(archive_path, trip_id)
    else:
        trip_ids = sorted(folder.name for folder in (data_root / "train").iterdir() if folder.is_dir())
        loader = lambda trip_id: _load_directory(data_root, trip_id)
    if len(trip_ids) != 80:
        raise ValueError(f"Expected 80 training trips, found {len(trip_ids)}.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_observations = total_recalled = total_rows = 0
    missed_by_trip = {}
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for trip_number, trip_id in enumerate(trip_ids, start=1):
            trip = loader(trip_id)
            nodes = trip["nodes"]
            arcs = trip["arcs"]
            track = trip["track"]
            route = trip["route"]
            network = build_road_network(nodes, arcs)
            points_xy = [network.projection.project(point[0], point[1]) for point in track]
            expected_arc_ids = align_reference_route(points_xy, route, network)
            rows = build_candidate_table(
                trip, candidate_radius_m=candidate_radius_m,
                include_labels=True, max_candidates=5,
            )
            report = candidate_recall_report(rows, expected_arc_ids, trip_id)
            positive_observations = {row["observation_idx"] for row in rows if row["label"] == 1}
            missing_positive = sorted(set(range(len(track))) - positive_observations)
            if len(missing_positive) != report["missed"]:
                raise RuntimeError(f"Positive-label and recall counts disagree for trip {trip_id}.")
            writer.writerows(rows)
            total_observations += len(track)
            total_recalled += report["recalled"]
            total_rows += len(rows)
            missed_by_trip[trip_id] = missing_positive
            print(f"[{trip_number}/80] trip {trip_id}: {len(track)} observations, "
                  f"{len(rows)} rows, {report['missed']} missing positives")
    return {
        "trips": len(trip_ids),
        "observations": total_observations,
        "candidate_rows": total_rows,
        "recalled_observations": total_recalled,
        "missed_observations": total_observations - total_recalled,
        "candidate_recall": total_recalled / total_observations if total_observations else None,
        "missed_by_trip": missed_by_trip,
        "output_path": str(output_path),
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, help="Extracted Student folder directory.")
    parser.add_argument("--archive", type=Path, help="Outer materials ZIP or Student folder ZIP.")
    parser.add_argument("--output", type=Path, default=Path("data/processed/train_features.csv"))
    parser.add_argument("--candidate-radius-m", type=float, default=100.0)
    args = parser.parse_args()
    report = generate(args.data_root, args.archive, args.output, args.candidate_radius_m)
    print("\nAggregate candidate coverage (against the documented route-alignment heuristic):")
    print(f"Trips: {report['trips']}")
    print(f"GPS observations: {report['observations']}")
    print(f"Candidate rows: {report['candidate_rows']}")
    print(f"Positive candidate recall: {report['candidate_recall']:.4%}")
    print(f"Observations with no positive candidate: {report['missed_observations']}")
    print(f"CSV: {report['output_path']}")
    print("Labels remain heuristic because the route file has no per-observation timestamps.")

if __name__ == "__main__":
    main()
