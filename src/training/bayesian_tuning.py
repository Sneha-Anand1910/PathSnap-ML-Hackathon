"""Tune Gradient Boosting on training trips only with grouped cross-validation."""

import argparse
import json
from pathlib import Path
from time import perf_counter

import joblib
import optuna
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline

try:
    from .model_configs import get_model_configs
    from .train_models import FEATURE_COLUMNS, load_data
except ImportError:  # Direct script execution from the repository root.
    from model_configs import get_model_configs
    from train_models import FEATURE_COLUMNS, load_data


def tuned_pipeline(params):
    return make_pipeline(
        SimpleImputer(strategy="median"),
        GradientBoostingClassifier(random_state=42, **params),
    )


def cv_macro_f1(factory, features, labels, folds):
    """Fit a fresh imputation pipeline inside each training fold."""
    scores = []
    for train_idx, valid_idx in folds:
        pipeline = factory()
        pipeline.fit(features.iloc[train_idx], labels.iloc[train_idx])
        predicted = pipeline.predict(features.iloc[valid_idx])
        scores.append(f1_score(labels.iloc[valid_idx], predicted,
                               average="macro", zero_division=0))
    return sum(scores) / len(scores)


def trial_rows(study, mode):
    return [{
        "trial": trial.number,
        "status": trial.state.name,
        "macro_f1": trial.value,
        "mode": mode,
        **trial.params,
    } for trial in study.trials]


def run(input_csv, output_dir, quick=False, trials=None, quick_trips=10):
    if trials is None:
        trials = 5 if quick else 20
    if trials < 1:
        raise ValueError("--trials must be at least 1")
    data = load_data(input_csv)
    mode = "quick_preliminary" if quick else "full"
    if quick:
        trip_ids = sorted(data["trip_id"].unique())
        if quick_trips < 3 or quick_trips > len(trip_ids):
            raise ValueError("--quick-trips must be between 3 and the number of training trips")
        chosen = pd.Series(trip_ids).sample(n=quick_trips, random_state=42).tolist()
        data = data.loc[data["trip_id"].isin(chosen)]
    features = data.loc[:, list(FEATURE_COLUMNS)]
    labels = data["label"].astype(int)
    if labels.nunique() != 2:
        raise ValueError("Selected trips must contain both binary labels")
    folds = list(GroupKFold(n_splits=3 if quick else 5).split(
        features, labels, data["trip_id"]
    ))
    if any(labels.iloc[train_idx].nunique() != 2 for train_idx, _ in folds):
        raise ValueError("Every training fold must contain both binary labels")

    destination = Path(output_dir) / mode
    destination.mkdir(parents=True, exist_ok=True)
    trial_csv = destination / "trials.csv"
    study = optuna.create_study(
        direction="maximize", sampler=optuna.samplers.TPESampler(seed=42, n_startup_trials=2)
    )

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 200, step=25),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.2, log=True),
            "max_depth": trial.suggest_int("max_depth", 2, 5),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 5, 50),
        }
        return cv_macro_f1(lambda: tuned_pipeline(params), features, labels, folds)

    def save_trials(study, _trial):
        pd.DataFrame(trial_rows(study, mode)).to_csv(trial_csv, index=False)

    optimization_start = perf_counter()
    study.optimize(objective, n_trials=trials, callbacks=[save_trials])
    optimization_seconds = perf_counter() - optimization_start

    baseline_start = perf_counter()
    baseline_score = cv_macro_f1(
        lambda: get_model_configs()["Gradient Boosting"], features, labels, folds
    )
    baseline_cv_seconds = perf_counter() - baseline_start
    best_params = study.best_params
    # The tuned score and baseline score use exactly the same rows and folds.
    comparison = pd.DataFrame([
        {"model": "Gradient Boosting baseline", "macro_f1": baseline_score,
         "cv_seconds": baseline_cv_seconds, "mode": mode},
        {"model": "Gradient Boosting tuned", "macro_f1": study.best_value,
         "cv_seconds": None, "mode": mode},
    ])
    comparison.to_csv(destination / "comparison.csv", index=False)
    with (destination / "best_params.json").open("w", encoding="utf-8") as file:
        json.dump({"mode": mode, "preliminary": quick, "parameters": best_params,
                   "cv_macro_f1": study.best_value, "folds": len(folds),
                   "trips": int(data["trip_id"].nunique()),
                   "optimization_seconds": optimization_seconds,
                   "baseline_cv_seconds": baseline_cv_seconds}, file, indent=2)

    training_start = perf_counter()
    model = tuned_pipeline(best_params)
    model.fit(features, labels)
    joblib.dump(model, destination / "model.joblib")
    training_seconds = perf_counter() - training_start
    with (destination / "timing.json").open("w", encoding="utf-8") as file:
        json.dump({"mode": mode, "preliminary": quick,
                   "optimization_seconds": optimization_seconds,
                   "baseline_cv_seconds": baseline_cv_seconds,
                   "final_training_and_save_seconds": training_seconds}, file, indent=2)
    print(comparison.to_string(index=False))
    print(f"Saved {mode} outputs to {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", help="Training candidate CSV, including .csv.gz")
    parser.add_argument("--output-dir", default="results/training/bayesian-tuning")
    parser.add_argument("--trials", type=int, help="Optuna trials (default: 5 quick, 20 full)")
    parser.add_argument("--quick", action="store_true", help="Preliminary 3-fold run on sampled training trips")
    parser.add_argument("--quick-trips", type=int, default=10,
                        help="Training trips in quick mode (default: 10)")
    args = parser.parse_args()
    run(args.input_csv, args.output_dir, quick=args.quick, trials=args.trials,
        quick_trips=args.quick_trips)


if __name__ == "__main__":
    main()
