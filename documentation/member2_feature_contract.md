# Member 2: candidate generation and feature contract

Input stays Member 1's dictionary with trip_id, track, nodes, arcs, and route. The loader output is not modified. Nodes and arcs retain row order; Dataset Exploration confirms arc IDs are zero-based .arcs row positions.

Rows include trip_id, observation_idx, candidate_arc_id, candidate_rank, distance_m, projection_x_m, projection_y_m, along_arc_fraction, bearing_difference, label, speed_mps, time_gap_s and geometry metadata. IDs are join/decoder keys and should not enter the numeric model feature matrix by default.

Route labels are created only when build_candidate_table(trip, include_labels=True) is called. The alignment spatially shortlists route occurrences, then uses dynamic programming with distance emissions and a forward-advance penalty. Route position may stay or advance, never retreat. This is a heuristic because .route has no direct GPS timestamp mapping; validate it with the team before final model selection. The default include_labels=False keeps route references out of inference.

candidate_recall_report compares expected aligned arc IDs with generated candidates and reports missed observations and recall. Tune candidate radius using training and student-development trips only. Do not use evaluator ground truth for feature creation or model selection.
