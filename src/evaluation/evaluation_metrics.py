
"""
PathSnap - Evaluation Metrics
Member 4: Shruti

Implements classification, observation-level ranking,
probability and candidate-generation evaluation metrics.
"""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    log_loss
)


def calculate_classification_metrics(y_true, y_pred):
    """
    Calculate binary classification metrics.

    1 = Correct candidate
    0 = Incorrect candidate
    """

    return {
        "accuracy": accuracy_score(y_true, y_pred),

        "precision": precision_score(
            y_true, y_pred,
            average="binary",
            zero_division=0
        ),

        "recall": recall_score(
            y_true, y_pred,
            average="binary",
            zero_division=0
        ),

        "macro_f1": f1_score(
            y_true, y_pred,
            average="macro",
            zero_division=0
        )
    }


def calculate_top1_accuracy(
    trip_ids,
    observation_ids,
    y_true,
    y_scores
):
    """
    Calculate observation-level Top-1 Accuracy.

    Each GPS observation is uniquely identified by
    its trip_id and observation_id.
    """

    import numpy as np

    trip_ids = np.asarray(trip_ids)
    observation_ids = np.asarray(observation_ids)
    y_true = np.asarray(y_true)
    y_scores = np.asarray(y_scores)

    if not (
        len(trip_ids) == len(observation_ids)
        == len(y_true) == len(y_scores)
    ):
        raise ValueError("All input arrays must have equal lengths.")

    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty.")

    if not np.isin(y_true, [0, 1]).all():
        raise ValueError("Labels must be binary: 0 or 1.")

    if not np.isfinite(y_scores).all():
        raise ValueError("Scores must be finite.")

    observation_groups = {}

    for i, key in enumerate(zip(trip_ids, observation_ids)):
        observation_groups.setdefault(key, []).append(i)

    observation_results = []

    for indices in observation_groups.values():

        best_index = indices[np.argmax(y_scores[indices])]

        observation_results.append(y_true[best_index] == 1)

    return float(np.mean(observation_results))


def calculate_log_loss(y_true, y_prob):
    """
    Calculate binary Log Loss using positive-class probabilities.
    """

    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    if len(y_true) != len(y_prob):
        raise ValueError("Labels and probabilities must have equal lengths.")

    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty.")

    if not np.isfinite(y_prob).all():
        raise ValueError("Probabilities must be finite.")

    if np.any((y_prob < 0) | (y_prob > 1)):
        raise ValueError("Probabilities must be between 0 and 1.")

    return log_loss(
        y_true,
        y_prob,
        labels=[0, 1]
    )


def calculate_candidate_miss_rate(
    observation_ids,
    candidate_arc_ids,
    true_arc_ids
):
    """
    Calculate Candidate Miss Rate.

    Parameters
    ----------
    observation_ids : array-like
        GPS observation ID for every candidate row.

    candidate_arc_ids : array-like
        Candidate road segment ID for every row.

    true_arc_ids : dict
        Mapping of observation ID to its reference road segment ID.

    Returns
    -------
    float
        Fraction of observations where the true road
        segment is absent from the candidate list.
    """

    observation_ids = np.asarray(observation_ids)
    candidate_arc_ids = np.asarray(candidate_arc_ids)

    if len(observation_ids) != len(candidate_arc_ids):
        raise ValueError("Input arrays must have equal lengths.")

    if len(observation_ids) == 0:
        raise ValueError("Input arrays cannot be empty.")

    unique_observations = np.unique(observation_ids)

    misses = 0

    for obs_id in unique_observations:

        if obs_id not in true_arc_ids:
            raise ValueError(
                f"Missing reference arc ID for observation {obs_id}"
            )

        indices = np.where(observation_ids == obs_id)[0]

        candidates = set(candidate_arc_ids[indices])

        true_arc = true_arc_ids[obs_id]

        if true_arc not in candidates:
            misses += 1

    return misses / len(unique_observations)

