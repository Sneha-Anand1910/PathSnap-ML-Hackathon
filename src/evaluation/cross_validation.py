
"""
PathSnap - Group-Aware Cross Validation
Member 4: Shruti

Implements 5-fold GroupKFold using trip_id.
Ensures observations from the same trip never
appear in both training and validation sets.
"""

import numpy as np
from sklearn.model_selection import GroupKFold


def create_group_folds(
    X,
    groups,
    n_splits=5
):
    """
    Generate group-aware cross-validation folds.

    Parameters
    ----------
    X : array-like
        Feature matrix.
    groups : array-like
        Group identifier for each observation (trip_id).
    n_splits : int
        Number of folds. Default is 5.

    Returns
    -------
    list
        List of (train_indices, validation_indices).
    """

    groups = np.asarray(groups)

    if len(X) != len(groups):
        raise ValueError(
            "X and groups must contain the same number of rows."
        )

    if pd_is_missing(groups):
        raise ValueError("Group IDs cannot contain missing values.")

    unique_groups = np.unique(groups)

    if len(unique_groups) < n_splits:
        raise ValueError(
            f"Need at least {n_splits} unique groups, "
            f"but found {len(unique_groups)}."
        )

    splitter = GroupKFold(n_splits=n_splits)

    folds = []

    for fold_number, (train_idx, val_idx) in enumerate(
        splitter.split(X, groups=groups), start=1
    ):
        train_groups = set(groups[train_idx])
        val_groups = set(groups[val_idx])

        # Verify that no trip appears in both sets.
        if train_groups.intersection(val_groups):
            raise RuntimeError(
                f"Data leakage detected in fold {fold_number}!"
            )

        folds.append((train_idx, val_idx))

    return folds


def pd_is_missing(values):
    """Check for missing group identifiers."""
    import pandas as pd
    return pd.isna(values).any()


def validate_group_folds(folds, groups):
    """
    Verify that all generated folds have no group overlap.
    """

    groups = np.asarray(groups)

    for fold_number, (train_idx, val_idx) in enumerate(
        folds, start=1
    ):
        train_groups = set(groups[train_idx])
        val_groups = set(groups[val_idx])

        if train_groups.intersection(val_groups):
            raise ValueError(
                f"Group leakage found in fold {fold_number}."
            )

    return True

