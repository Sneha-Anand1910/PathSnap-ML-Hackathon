
"""
PathSnap - Model Result Visualization
Member 4: Shruti

Generates comparison graphs for ML model performance.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


def plot_metric_comparison(
    comparison_table,
    metric,
    title,
    output_path
):
    """
    Generate a bar chart comparing models using a metric.

    Parameters
    ----------
    comparison_table : pandas.DataFrame
        Aggregated model comparison results.

    metric : str
        Metric name, e.g. macro_f1 or accuracy.

    title : str
        Graph title.

    output_path : str
        Destination PNG file.
    """

    mean_column = f"{metric}_mean"
    std_column = f"{metric}_std"

    required_columns = ["model", mean_column]

    for column in required_columns:
        if column not in comparison_table.columns:
            raise ValueError(
                f"Missing required column: {column}"
            )

    data = comparison_table.dropna(
        subset=[mean_column]
    ).copy()

    if data.empty:
        raise ValueError("No valid results available to plot.")

    data = data.sort_values(
        by=mean_column,
        ascending=False
    )

    errors = None

    if std_column in data.columns:
        errors = data[std_column].fillna(0)

    plt.figure(figsize=(10, 6))

    plt.bar(
        data["model"].astype(str),
        data[mean_column],
        yerr=errors,
        capsize=5
    )

    plt.title(title)
    plt.xlabel("Machine Learning Models")
    plt.ylabel(metric.replace("_", " ").title())
    plt.xticks(rotation=25, ha="right")
    plt.ylim(0, 1.05)
    plt.grid(axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()

    directory = os.path.dirname(output_path)

    if directory:
        os.makedirs(directory, exist_ok=True)

    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Graph saved successfully: {output_path}")


def generate_all_comparison_graphs(
    comparison_table,
    results_dir="results"
):
    """
    Generate all required comparison graphs.
    """

    os.makedirs(results_dir, exist_ok=True)

    # Macro F1 comparison
    plot_metric_comparison(
        comparison_table,
        metric="macro_f1",
        title="Model Comparison - Macro F1 Score",
        output_path=os.path.join(
            results_dir,
            "f1_comparison.png"
        )
    )

    # Accuracy comparison
    plot_metric_comparison(
        comparison_table,
        metric="accuracy",
        title="Model Comparison - Accuracy",
        output_path=os.path.join(
            results_dir,
            "accuracy_comparison.png"
        )
    )

    print("\nAll comparison graphs generated successfully!")

