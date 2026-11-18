
import pandas as pd
from pathlib import Path

from evaluation_metrics import (
    calculate_classification_metrics,
    calculate_top1_accuracy,
    calculate_log_loss
)

from model_comparison import (
    summarize_cv_results,
    save_comparison_csv,
    select_best_model
)

from visualize_results import generate_all_comparison_graphs


def run_evaluation(prediction_file):

    # Load OOF predictions
    df = pd.read_csv(prediction_file)

    required_columns = [
        "model", "fold", "trip_id",
        "observation_id", "candidate_arc_id",
        "y_true", "y_pred", "y_prob"
    ]

    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if df.empty:
        raise ValueError("Prediction file is empty.")

    if not df["y_true"].isin([0, 1]).all():
        raise ValueError("y_true must contain only 0 and 1.")

    if not df["y_pred"].isin([0, 1]).all():
        raise ValueError("y_pred must contain only 0 and 1.")

    if not df["y_prob"].between(0, 1).all():
        raise ValueError("y_prob must be between 0 and 1.")

    results = []

    # Calculate metrics for each model and fold
    for (model, fold), group in df.groupby(["model", "fold"]):

        y_true = group["y_true"].to_numpy()
        y_pred = group["y_pred"].to_numpy()
        y_prob = group["y_prob"].to_numpy()

        metrics = calculate_classification_metrics(
            y_true, y_pred
        )

        metrics["top1_accuracy"] = calculate_top1_accuracy(
            group["trip_id"].to_numpy(),
            group["observation_id"].to_numpy(),
            y_true,
            y_prob
        )

        metrics["log_loss"] = calculate_log_loss(
            y_true, y_prob
        )

        metrics["model"] = model
        metrics["fold"] = fold

        results.append(metrics)

    # Create results folder
    Path("results").mkdir(exist_ok=True)

    results_df = pd.DataFrame(results)

    # Save fold-wise metrics
    results_df.to_csv(
        "results/fold_wise_metrics.csv",
        index=False
    )

    # Create model comparison table
    comparison_df = summarize_cv_results(results_df)

    save_comparison_csv(
        comparison_df,
        "results/model_comparison.csv"
    )

    # Generate comparison graphs
    generate_all_comparison_graphs(
        comparison_df,
        results_dir="results"
    )

    # Select best model based on Macro F1
    best_model = select_best_model(comparison_df)

    print("\nEVALUATION COMPLETED")
    print("\nFold-wise metrics:")
    print(results_df)

    print("\nModel comparison:")
    print(comparison_df)

    print("\nBest model based on Macro F1:")
    print(best_model)

    return results_df, comparison_df


if __name__ == "__main__":
    run_evaluation("results/sample_oof_predictions.csv")

