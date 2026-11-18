
# PathSnap Data Preprocessing

## 1. Dataset Structure

Each trip contains four files:

- `.track`: GPS observations (longitude, latitude, timestamp)
- `.nodes`: Road network node coordinates
- `.arcs`: Connections between road network nodes
- `.route`: Ordered route arc IDs

## 2. Data Loading

The `data_loader.py` module loads the four files into Pandas DataFrames.

The `load_trip()` function returns a dictionary containing:

- trip_id
- track
- nodes
- arcs
- route

This output format is maintained for compatibility with downstream feature engineering.

## 3. Validation Checks

The `data_validator.py` module checks:

- Missing values
- Duplicate records
- GPS coordinate validity
- Timestamp ordering and duplicates
- Invalid road network references
- Invalid route arc IDs
- Connectivity between consecutive route segments

## 4. Cleaning and Transformation

The current pipeline performs data loading and validation.

It does not automatically delete duplicates, remove GPS observations, modify routes, or discard trips.

The original data is preserved so that downstream feature engineering can use it without unintended changes.

Any additional cleaning will be introduced separately after investigating validation findings.

## 5. Validation Findings

The initial validation run processed 80 training trips.

Ten trips were flagged for disconnected consecutive route segments.

These trips are retained and their warnings are documented for further investigation.

## 6. Output Reports

The preprocessing script generates:

- `results/preprocessing/validation_summary.csv`
- `results/preprocessing/all_trips_validation.txt`

## 7. Running the Pipeline

From the repository root:

```bash
python3 -m src.preprocessing.preprocess --data-dir "/path/to/train"
```

The dataset path can also be supplied using the `PATHSNAP_DATA_DIR` environment variable.
