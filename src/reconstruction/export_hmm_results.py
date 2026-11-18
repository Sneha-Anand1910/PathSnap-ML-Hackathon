"""Export private Gradient Boosting + HMM evaluation for 10 student-testing trips.

This is an offline report. It never sends reference routes through the API.
"""

import argparse
import csv
import json
import re
from pathlib import Path

import joblib
import pandas as pd

from src.features.create_training_data import align_reference_route, build_candidate_table
from src.features.feature_engineering import GPSObservation, extract_gps_features
from src.features.road_network import build_road_network
from src.reconstruction.evaluation import evaluate_route
from src.reconstruction.hmm_viterbi import (
    gps_step_distances, group_candidate_rows, viterbi_decode,
)
from src.training.train_models import FEATURE_COLUMNS, SOURCE_COLUMNS


def read_rows(path, names):
    if not path.is_file():
        raise FileNotFoundError(f"Missing trip file: {path}")
    frame = pd.read_csv(path, sep=r"\s+", header=None, names=names)
    if frame.empty or frame.isna().any().any():
        raise ValueError(f"Empty or incomplete trip file: {path}")
    return frame


def evaluate_trip(folder, model):
    trip_id = folder.name
    track = read_rows(folder / f"{trip_id}.track", ["longitude", "latitude", "timestamp"])
    nodes = read_rows(folder / f"{trip_id}.nodes", ["longitude", "latitude"])
    arcs = read_rows(folder / f"{trip_id}.arcs", ["from_node", "to_node"])
    network = build_road_network(nodes.itertuples(index=False, name=None),
                                 arcs.itertuples(index=False, name=None))
    if not network.segments:
        raise ValueError(f"Trip {trip_id} has no road arcs")
    observations = [GPSObservation(*row) for row in track.itertuples(index=False, name=None)]
    gps = extract_gps_features(observations, network.projection)
    points = [(row["x_m"], row["y_m"]) for row in gps]
    # Reference data is deliberately absent from feature generation and decoding.
    trip = {"trip_id": trip_id, "track": track, "nodes": nodes, "arcs": arcs, "route": []}
    candidates = build_candidate_table(trip, include_labels=False)
    if candidates:
        features = pd.DataFrame(candidates).rename(columns=SOURCE_COLUMNS)
        probabilities = model.predict_proba(features.loc[:, list(FEATURE_COLUMNS)])[
            :, list(model.classes_).index(1)
        ]
    else:
        probabilities = []
    grouped = group_candidate_rows(candidates, probabilities, len(track))
    decoded = viterbi_decode(grouped, network,
                             observed_distances_m=gps_step_distances(points),
                             projected_points_xy=points)
    predicted = decoded.predicted_arc_ids
    if len(predicted) != len(track) or any(arc_id is None for arc_id in predicted):
        raise ValueError(f"Trip {trip_id}: decoder did not produce one arc ID per observation")

    # Original ordered route and per-observation heuristic alignment are distinct.
    route = read_rows(folder / f"{trip_id}.route", ["arc_id"])
    original_route = route["arc_id"].astype(int).tolist()
    aligned_reference = align_reference_route(points, original_route, network)
    metrics = evaluate_route(predicted, aligned_reference, network)
    return {
        "trip_id": trip_id,
        "predicted_ordered_arc_ids": [int(arc_id) for arc_id in predicted],
        "reference_ordered_arc_ids": original_route,
        "aligned_reference_arc_ids_by_observation": aligned_reference,
        "accuracy": metrics["accuracy"],
        "accuracy_method": "heuristic per-observation alignment of the original .route sequence",
        "route_continuity_score": metrics["route_continuity"],
        "missing_candidates": len(decoded.empty_candidate_observations),
        "missing_candidate_observation_indices": decoded.empty_candidate_observations,
        "fallback_observations": len(decoded.fallback_observation_indices),
        "fallback_observation_indices": decoded.fallback_observation_indices,
        "disconnected_transitions": decoded.disconnected_transition_count,
        "observations": len(track),
        "candidate_rows": len(candidates),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True,
                        help="Parent directory of the 10 student-testing trip folders")
    parser.add_argument("--model", type=Path,
                        default=Path("results/training/gradient-boosting/model.joblib"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/evaluation/hmm"))
    args = parser.parse_args()
    if not args.data_dir.is_dir():
        parser.error(f"Student-testing directory not found: {args.data_dir}")
    if not args.model.is_file():
        parser.error(f"Pretrained model not found: {args.model}")
    folders = sorted(folder for folder in args.data_dir.iterdir()
                     if folder.is_dir() and re.fullmatch(r"[0-9]{8}", folder.name))
    if len(folders) != 10:
        parser.error(f"Expected 10 student-testing trip folders, found {len(folders)}")

    model = joblib.load(args.model)
    results = []
    for folder in folders:
        print(f"Evaluating {folder.name}", flush=True)
        results.append(evaluate_trip(folder, model))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "results.json"
    csv_path = args.output_dir / "results.csv"
    with json_path.open("w", encoding="utf-8") as file:
        json.dump({"evaluation_type": "heuristic-based student-testing evaluation",
                   "model": str(args.model), "trips": results}, file, indent=2)
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        for result in results:
            writer.writerow({key: json.dumps(value) if isinstance(value, list) else value
                             for key, value in result.items()})
    print(f"Saved {len(results)} trip results to {json_path} and {csv_path}")


if __name__ == "__main__":
    main()
