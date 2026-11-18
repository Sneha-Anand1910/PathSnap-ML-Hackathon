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


def load_data(input_path):
    """Load a labeled candidate CSV and validate the training contract."""
    path = Path(input_path)
    if not path.is_file():
        raise FileNotFoundError(f"Labeled candidate CSV not found: {path}")
    data = pd.read_csv(path)
    missing = sorted(set(REQUIRED_COLUMNS) - set(data.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if data.empty:
        raise ValueError("Labeled candidate CSV is empty")
    if data["trip_id"].isna().any():
        raise ValueError("trip_id must be present for every row")
    if data["trip_id"].nunique() < 5:
        raise ValueError("At least 5 distinct trips are required for 5-fold GroupKFold")
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


def compare_models(data, return_predictions=False):
    """Return mean 5-fold scores, best name, and optionally OOF predictions."""
    features = data.loc[:, list(FEATURE_COLUMNS)]
    labels = data["label"].astype(int)
    groups = data["trip_id"]
    splitter = GroupKFold(n_splits=5)
    rows = []
    predictions = []
    for name, pipeline in get_model_configs().items():
        fold_scores = []
        for fold, (train_idx, test_idx) in enumerate(splitter.split(features, labels, groups), start=1):
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


def train(input_path, results_path="results/training_results.csv", model_path="models/best_model.joblib",
          oof_path="results/training/oof_predictions.csv"):
    """Cross-validate, select by macro F1, and persist the final fit."""
    data = load_data(input_path)
    results, best_name, predictions = compare_models(data, return_predictions=True)
    best_model = get_model_configs()[best_name]
    best_model.fit(data.loc[:, list(FEATURE_COLUMNS)], data["label"].astype(int))
    results_file, model_file, oof_file = Path(results_path), Path(model_path), Path(oof_path)
    results_file.parent.mkdir(parents=True, exist_ok=True)
    model_file.parent.mkdir(parents=True, exist_ok=True)
    oof_file.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(results_file, index=False)
    predictions.to_csv(oof_file, index=False)
    joblib.dump(best_model, model_file)
    return results, best_name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", help="Path to a labeled candidate CSV")
    args = parser.parse_args()
    results, best_name = train(args.input_csv)
    print(results.to_string(index=False))
    print(f"Best model: {best_name}")


if __name__ == "__main__":
    main()
