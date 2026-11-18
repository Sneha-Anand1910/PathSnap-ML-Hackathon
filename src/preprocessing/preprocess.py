
from pathlib import Path
import argparse
import contextlib
import os

import pandas as pd

from .data_loader import load_trip
from .data_validator import validate_trip


# Project root: PathSnap-ML-Hackathon/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Reports are always saved inside the repository.
RESULTS_DIR = PROJECT_ROOT / "results" / "preprocessing"


def validate_all_trips(data_dir):
    """Load and validate every trip in the supplied training directory."""

    data_dir = Path(data_dir).expanduser()

    if not data_dir.exists():
        raise FileNotFoundError(
            f"Dataset directory not found: {data_dir}\n"
            "Provide the correct training directory using --data-dir "
            "or PATHSNAP_DATA_DIR."
        )

    if not data_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {data_dir}")

    trip_folders = sorted(
        folder for folder in data_dir.iterdir() if folder.is_dir()
    )

    if not trip_folders:
        raise ValueError(f"No trip folders found in: {data_dir}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Dataset directory:", data_dir)
    print("Total training trips:", len(trip_folders))

    summary = []
    report_path = RESULTS_DIR / "all_trips_validation.txt"

    with open(report_path, "w", encoding="utf-8") as report:
        for i, folder in enumerate(trip_folders, start=1):
            print(
                f"Processing trip {i}/{len(trip_folders)}: {folder.name}"
            )

            # Keep load_trip() output unchanged for feature engineering.
            trip = load_trip(folder)

            with contextlib.redirect_stdout(report):
                issues = validate_trip(trip)

            summary.append({
                "trip_id": trip["trip_id"],
                "issue_count": len(issues),
                "issues": "; ".join(issues)
            })

    summary_df = pd.DataFrame(summary)

    summary_path = RESULTS_DIR / "validation_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    print("\nVALIDATION COMPLETED")
    print("Trips processed:", len(summary_df))
    print(
        "Trips with validation warnings:",
        (summary_df["issue_count"] > 0).sum()
    )
    print("CSV report:", summary_path)
    print("Detailed report:", report_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate the PathSnap training dataset."
    )

    parser.add_argument(
        "--data-dir",
        default=os.environ.get("PATHSNAP_DATA_DIR"),
        help=(
            "Path to the training directory containing individual trip "
            "folders. Can also be set using PATHSNAP_DATA_DIR."
        )
    )

    args = parser.parse_args()

    if not args.data_dir:
        parser.error(
            "Dataset path required. Use --data-dir or set "
            "PATHSNAP_DATA_DIR."
        )

    validate_all_trips(args.data_dir)
