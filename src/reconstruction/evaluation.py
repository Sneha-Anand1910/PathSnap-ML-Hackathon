"""Classifier-only versus HMM route evaluation helpers.

Reference arc IDs are consumed here only for scoring after prediction. They must
not be passed into model prediction or viterbi_decode.
"""
from __future__ import annotations
from typing import Mapping, Sequence
from .hmm_viterbi import RoadTransitionGraph


def classifier_only_predictions(candidate_sequences, fallback_arc_ids=None):
    """Select the top-probability candidate independently at each observation."""
    predictions = []
    for index, states in enumerate(candidate_sequences):
        if not states:
            predictions.append(None if fallback_arc_ids is None else fallback_arc_ids[index])
            continue
        def probability(state):
            return float(state.get("probability", state.get("model_probability", state.get("score", 0.0))))
        predictions.append(int(max(states, key=probability).get(
            "candidate_arc_id", max(states, key=probability).get("arc_id")
        )))
    return predictions


def evaluate_route(predictions: Sequence[int | None],
                   reference_arc_ids: Sequence[int],
                   network,
                   *, max_connector_hops: int = 4) -> dict:
    """Score predictions after decoding; None counts as incorrect for accuracy."""
    if len(predictions) != len(reference_arc_ids):
        raise ValueError("Predictions and reference labels must have equal length.")
    correct = sum(pred == int(ref) for pred, ref in zip(predictions, reference_arc_ids))
    n = len(reference_arc_ids)
    graph = RoadTransitionGraph(network, max_connector_hops)
    segments = {segment.arc_id: segment for segment in network.segments}
    connected = considered = skipped = 0
    for previous_id, current_id in zip(predictions, predictions[1:]):
        if previous_id is None or current_id is None:
            skipped += 1
            continue
        considered += 1
        if previous_id == current_id:
            connected += 1
            continue
        previous_segment = segments.get(int(previous_id))
        current_segment = segments.get(int(current_id))
        if previous_segment is not None and current_segment is not None and graph.connector(
            previous_segment.to_node_id, current_segment.from_node_id
        ) is not None:
            connected += 1
    return {
        "accuracy": None if n == 0 else correct / n,
        "correct": correct,
        "observations": n,
        "prediction_coverage": None if n == 0 else sum(p is not None for p in predictions) / n,
        "route_continuity": None if considered == 0 else connected / considered,
        "connected_transitions": connected,
        "considered_transitions": considered,
        "skipped_transitions": skipped,
        "disconnected_transitions": considered - connected,
    }


def compare_classifier_and_hmm(candidate_sequences, reference_arc_ids, network,
                               hmm_predictions, *, max_connector_hops: int = 4):
    """Return comparable metrics for independent top-1 and HMM predictions."""
    baseline = classifier_only_predictions(candidate_sequences, hmm_predictions)
    return {
        "classifier_only": evaluate_route(
            baseline, reference_arc_ids, network, max_connector_hops=max_connector_hops
        ),
        "hmm_viterbi": evaluate_route(
            hmm_predictions, reference_arc_ids, network, max_connector_hops=max_connector_hops
        ),
    }
