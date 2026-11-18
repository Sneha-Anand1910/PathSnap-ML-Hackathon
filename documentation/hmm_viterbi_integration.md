# HMM/Viterbi integration handoff

## Decoder input

The backend loads the selected trip, builds its RoadNetwork, generates candidate rows, and calls the trained classifier. Group classifier results by observation index, preserving one list of candidate mappings per GPS observation.

Each mapping must contain:

- candidate_arc_id: row-position arc ID from the arcs file
- probability: classifier probability for that candidate
- from_node_id and to_node_id: directed arc endpoints
- road_length_m: segment length in metres
- along_arc_fraction: projected point position from 0 at the arc start to 1 at its end

Optional observed_distances_m contains the projected GPS displacement between each consecutive observation and has length N-1.

## Decoder call

    from src.reconstruction import viterbi_decode

    result = viterbi_decode(
        candidate_sequences,
        network,
        observed_distances_m=observed_distances_m,
        projected_points_xy=points_xy,
    )

## Decoder output

DecodeResult contains:

- predicted_arc_ids: one arc ID per GPS observation when projected points are supplied; nearest-network fallback for empty candidate lists
- log_score: score of the selected decoded sequence
- decoded_observations: count with at least one candidate
- empty_candidate_observations: indices where candidate generation returned no rows
- fallback_observation_indices: which of those used nearest-network fallback
- disconnected_transition_count: transitions that needed the disconnected fallback penalty

The decoder uses model probabilities as emissions. It rewards transitions along directed, connected roads and compares road-path distance with GPS displacement. If a candidate list is empty, it decodes the sequence segments on either side independently and uses the nearest network arc as a flagged fallback when projected GPS coordinates are supplied.

## Proposed UI/API flow

The evaluator-facing UI should send only a trip ID to the backend. The backend loads data, gets model probabilities, calls the decoder, and returns predicted_arc_ids plus allowed aggregate metrics. Keep the reference route and per-observation labels on the backend; do not return them in the API response.

The PDF specifies this trip-ID flow and server-side ground-truth handling but does not define exact JSON field names. Confirm the proposed /predict request and response in api_contract_proposal.md with the API and UI owners.

## Limits to communicate

The candidate generator's top-five limit can omit the reference arc. The decoder cannot select an arc absent from the candidate list. The route labels are also heuristic because .route contains sequence order but no direct GPS timestamp mapping. Tune transition settings with training and student-development trips only, and compare classifier-only versus HMM output.


Evaluation helpers compare independent top-probability candidate selection against HMM output using observation accuracy and directed route continuity. Reference arc IDs are only used after decoding for scoring and must not enter prediction.
