
"""
PathSnap - Model Comparison
Member 4: Shruti

Aggregates cross-validation results from different ML models,
creates a consolidated comparison table and identifies
the best-performing model based on Macro F1.
"""

import os
import pandas as pd


METRIC_COLUMNS = [
    "accuracy",
    "precision",
    "recall",
    "macro_f1",
    "top1_accuracy",
    "log_loss",
    "candidate_miss_rate"
]


def summarize_cv_results(fold_results):
    """
    Aggregate evaluation metrics across cross-validation folds.
    """

    if not fold_results:
        raise ValueError("No model results were provided.")

    df = pd.DataFrame(fold_results)

    if not {"model", "fold"}.issubset(df.columns):
        raise ValueError("Missing model or fold columns.")

    if df[["model", "fold"]].isnull().any().any():
        raise ValueError("Model names and fold numbers cannot be missing.")

    available_metrics = [
        metric for metric in METRIC_COLUMNS
        if metric in df.columns
    ]

    if not available_metrics:
        raise ValueError("No evaluation metrics were provided.")

    for metric in available_metrics:
        df[metric] = pd.to_numeric(df[metric], errors="raise")

    if df[available_metrics].isnull().any().any():
        raise ValueError("Metric values cannot be missing.")

    # Calculate mean and standard deviation separately.
    means = df.groupby("model")[available_metrics].mean()
    stds = df.groupby("model")[available_metrics].std()

    summary = pd.concat(
        [means.add_suffix("_mean"), stds.add_suffix("_std")],
        axis=1
    ).reset_index()

    fold_counts = (
        df.groupby("model")["fold"]
        .nunique()
        .rename("n_folds")
        .reset_index()
    )

    summary = summary.merge(fold_counts, on="model")

    return summary

def save_comparison_csv(
    comparison_table,
    output_path="results/model_comparison.csv"
):
    """
    Save the model comparison table as a CSV file.
    """

    directory = os.path.dirname(output_path)

    if directory:
        os.makedirs(directory, exist_ok=True)

    comparison_table.to_csv(output_path, index=False)

    print(f"Comparison results saved to: {output_path}")


def select_best_model(
    comparison_table,
    metric="macro_f1_mean"
):
    """
    Select the best model using the chosen metric.

    Higher scores are better for Macro F1,
    Accuracy, Precision, Recall and Top-1 Accuracy.
    """

    if metric not in comparison_table.columns:
        raise ValueError(f"Metric '{metric}' not found.")

    valid_results = comparison_table.dropna(subset=[metric])

    if valid_results.empty:
        raise ValueError("No valid model results available.")

    best_index = valid_results[metric].idxmax()

    return valid_results.loc[best_index]


def compare_models(
    fold_results,
    output_path="results/model_comparison.csv"
):
    """
    Complete model comparison workflow.
    """

    comparison_table = summarize_cv_results(fold_results)

    save_comparison_csv(comparison_table, output_path)

    best_model = select_best_model(comparison_table)

    print("\nModel Comparison:")
    print(comparison_table.to_string(index=False))

    print("\nBest Model based on Mean Macro F1:")
    print(best_model["model"])

    return comparison_table, best_model

