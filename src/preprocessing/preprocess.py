
from pathlib import Path
import pandas as pd
import contextlib

from data_loader import load_trip
from data_validator import validate_trip


# Dataset location
DATA_DIR = (
    Path.home()
    / "Downloads"
    / "Student folder"
    / "train"
)

# Results location
RESULTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "results"
    / "preprocessing"
)

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def validate_all_trips():

    trip_folders = sorted(
        folder for folder in DATA_DIR.iterdir()
        if folder.is_dir()
    )

    print("Total training trips:", len(trip_folders))

    summary = []

    report_path = RESULTS_DIR / "all_trips_validation.txt"

    with open(report_path, "w") as report:

        for i, folder in enumerate(trip_folders, start=1):

            print(
                f"Processing trip {i}/{len(trip_folders)}:"
                f" {folder.name}"
            )

            trip = load_trip(folder)

            with contextlib.redirect_stdout(report):
                issues = validate_trip(trip)

            summary.append({
                "trip_id": trip["trip_id"],
                "issue_count": len(issues),
                "issues": "; ".join(issues)
            })

    summary_df = pd.DataFrame(summary)

    summary_df.to_csv(
        RESULTS_DIR / "validation_summary.csv",
        index=False
    )

    print("\nVALIDATION COMPLETED")
    print("Trips processed:", len(summary_df))
    print(
        "Trips with warnings:",
        (summary_df["issue_count"] > 0).sum()
    )

    print("Reports saved in:", RESULTS_DIR)


if __name__ == "__main__":
    validate_all_trips()
