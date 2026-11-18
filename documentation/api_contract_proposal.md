# Proposed UI/API contract

The assignment requires the UI to send a selected trip ID to the backend. The backend runs the prediction pipeline and keeps reference labels server-side. The PDFs do not prescribe exact JSON field names; this is a proposed contract for the API and UI owners to confirm.

## Request

POST /predict

    {
      "trip_id": "00000001"
    }

The UI sends only the trip identifier. It does not send candidate labels, route IDs, model scores, or ground truth.

## Response

    {
      "trip_id": "00000001",
      "predicted_arc_ids": [64973, 133948, 133949],
      "observation_count": 3,
      "diagnostics": {
        "empty_candidate_observation_indices": [2],
        "fallback_observation_indices": [2],
        "disconnected_transition_count": 0
      },
      "metrics": {
        "observation_accuracy": 0.83,
        "candidate_miss_rate": 0.12,
        "route_continuity": 0.95
      }
    }

predicted_arc_ids[i] is the reconstructed road arc for GPS observation i. The decoder returns one arc ID per observation when projected GPS coordinates are provided. It falls back to the geometrically nearest network arc where candidate generation returned no candidates and reports those indices. The response must not include the reference route or per-observation ground-truth labels. The backend may compute metrics internally and return aggregate results if allowed by the evaluation design. Candidate miss rate is distinct from an empty candidate list: it means the reference arc was absent from a nonempty candidate set and can only be computed server-side using reference data.

## Backend decoder interface

Model feature columns, in order, are distance_m, bearing_difference, road_length_m, speed_mps, time_gap_s, candidate_rank, and along_arc_fraction. Use the positive-class output, for example predict_proba(X)[:, 1], as each candidate's probability.

Each candidate mapping passed to the decoder contains candidate_arc_id, probability, from_node_id, to_node_id, road_length_m, and along_arc_fraction. The helper group_candidate_rows attaches probabilities and creates one candidate list per observation. gps_step_distances can provide observed metric displacement between adjacent GPS points.

The Viterbi decoder consumes these scores, projected GPS coordinates, and the directed road graph. It returns one arc ID per observation; for empty candidate lists it uses the nearest network arc as a flagged geometric fallback. Disconnected transitions are penalized and counted.
