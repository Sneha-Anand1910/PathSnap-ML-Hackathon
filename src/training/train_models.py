"""Compare candidate classifiers by trip and save the best fitted pipeline."""

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import GroupKFold

try:
    from .model_configs import get_model_configs
except ImportError:  # Support direct script execution.
    from model_configs import get_model_configs


FEATURE_COLUMNS = (
    "distance_to_arc_m",
    "heading_diff_deg",
    "arc_length_m",
    "gps_speed_mps",
    "time_gap_s",
    "candidate_rank",
    "projection_fraction",
)
REQUIRED_COLUMNS = (*FEATURE_COLUMNS, "trip_id", "observation_id", "candidate_arc_id", "label")
SOURCE_COLUMNS = {
    "observation_idx": "observation_id",
    "distance_m": "distance_to_arc_m",
    "bearing_difference": "heading_diff_deg",
    "road_length_m": "arc_length_m",
    "speed_mps": "gps_speed_mps",
    "along_arc_fraction": "projection_fraction",
}


def load_data(input_path):
    """Load a labeled candidate CSV and validate the training contract."""
    path = Path(input_path)
    if not path.is_file():
        raise FileNotFoundError(f"Labeled candidate CSV not found: {path}")
    available = pd.read_csv(path, nrows=0).columns
    missing = sorted(
        column for column in REQUIRED_COLUMNS
        if column not in available and not any(
            source in available for source, target in SOURCE_COLUMNS.items() if target == column
        )
    )
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    source_names = {column: next(
        (source for source, target in SOURCE_COLUMNS.items()
         if target == column and source in available), column
    ) for column in REQUIRED_COLUMNS}
    data = pd.read_csv(path, usecols=list(source_names.values())).rename(
        columns={source: target for target, source in source_names.items()}
    )
    if data.empty:
        raise ValueError("Labeled candidate CSV is empty")
    if data["trip_id"].isna().any():
        raise ValueError("trip_id must be present for every row")
    if data["trip_id"].nunique() < 5:
        raise ValueError("At least 5 distinct trips are required for 5-fold GroupKFold")
    if data.duplicated(["trip_id", "observation_id", "candidate_arc_id"]).any():
        raise ValueError("Duplicate (trip_id, observation_id, candidate_arc_id) combinations found")
    if data["label"].isna().any() or not data["label"].isin([0, 1]).all():
        raise ValueError("Labels must contain only 0 and 1, with no missing values")
    if data["label"].nunique() != 2:
        raise ValueError("Labels must include both 0 and 1")
    for column in FEATURE_COLUMNS:
        try:
            data[column] = pd.to_numeric(data[column], errors="raise")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Feature {column} must contain numeric values or missing values") from exc
        if data[column].isna().all():
            raise ValueError(f"Feature {column} has no non-missing values")
    return data


MODEL_NAMES = {
    "logistic-regression": "Logistic Regression",
    "knn": "KNN",
    "decision-tree": "Decision Tree",
    "random-forest": "Random Forest",
    "gradient-boosting": "Gradient Boosting",
}


def compare_models(data, return_predictions=False, models=None):
    """Return mean 5-fold scores, best name, and optionally OOF predictions."""
    features = data.loc[:, list(FEATURE_COLUMNS)]
    labels = data["label"].astype(int)
    groups = data["trip_id"]
    splitter = GroupKFold(n_splits=5)
    rows = []
    predictions = []
    configurations = get_model_configs()
    selected = models or list(configurations)
    for name in selected:
        pipeline = configurations[name]
        fold_scores = []
        for fold, (train_idx, test_idx) in enumerate(splitter.split(features, labels, groups), start=1):
            print(f"{name}: fold {fold}/5", flush=True)
            pipeline.fit(features.iloc[train_idx], labels.iloc[train_idx])
            predicted = pipeline.predict(features.iloc[test_idx])
            probability = pipeline.predict_proba(features.iloc[test_idx])[:, list(pipeline.classes_).index(1)]
            actual = labels.iloc[test_idx]
            fold_predictions = data.iloc[test_idx][
                ["trip_id", "observation_id", "candidate_arc_id"]
            ].copy()
            fold_predictions.insert(0, "fold", fold)
            fold_predictions.insert(0, "model", name)
            fold_predictions["y_true"] = actual.to_numpy()
            fold_predictions["y_pred"] = predicted
            fold_predictions["y_prob"] = probability
            predictions.append(fold_predictions)
            fold_scores.append({
                "accuracy": accuracy_score(actual, predicted),
                "precision": precision_score(actual, predicted, zero_division=0),
                "recall": recall_score(actual, predicted, zero_division=0),
                "macro_f1": f1_score(actual, predicted, average="macro", zero_division=0),
            })
        means = pd.DataFrame(fold_scores).mean().to_dict()
        rows.append({"model": name, **means})
    results = pd.DataFrame(rows).sort_values("macro_f1", ascending=False, kind="stable")
    if return_predictions:
        return results, results.iloc[0]["model"], pd.concat(predictions, ignore_index=True)
    return results, results.iloc[0]["model"]


def train(input_path, models=None, output_dir="results/training"):
    """Cross-validate and save each selected model in its own directory."""
    data = load_data(input_path)
    selected = list(MODEL_NAMES) if models is None else models
    if not selected or any(name not in MODEL_NAMES for name in selected):
        raise ValueError(f"Models must be selected from: {', '.join(MODEL_NAMES)}")
    output_dir = Path(output_dir)
    rows = []
    for slug in dict.fromkeys(selected):
        name = MODEL_NAMES[slug]
        results, _, predictions = compare_models(data, return_predictions=True, models=[name])
        model_dir = output_dir / slug
        model_dir.mkdir(parents=True, exist_ok=True)
        results.to_csv(model_dir / "training_results.csv", index=False)
        predictions.to_csv(model_dir / "oof_predictions.csv", index=False)
        print(f"{name}: refitting on all trips", flush=True)
        fitted = get_model_configs()[name]
        fitted.fit(data.loc[:, list(FEATURE_COLUMNS)], data["label"].astype(int))
        joblib.dump(fitted, model_dir / "model.joblib")
        rows.append(results.iloc[0])
    comparison = pd.DataFrame(rows).sort_values("macro_f1", ascending=False, kind="stable")
    best_name = comparison.iloc[0]["model"]
    return comparison, best_name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", help="Path to a labeled candidate CSV")
    parser.add_argument("--models", nargs="+", choices=MODEL_NAMES, metavar="MODEL",
                        help=f"Models to train: {', '.join(MODEL_NAMES)} (default: all)")
    parser.add_argument("--output-dir", default="results/training",
                        help="Base directory for separate per-model artifacts")
    args = parser.parse_args()
    results, best_name = train(args.input_csv, models=args.models, output_dir=args.output_dir)
    print(results.to_string(index=False))
    print(f"Best model: {best_name}")


if __name__ == "__main__":
    main()
