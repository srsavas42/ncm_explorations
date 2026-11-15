# Opposite-answer follow-up · pilot

Status: complete. The predeclared primary is the directional rule shift, with positive predicted. Intervals below are 95% percentile resamples of whole families.

| Transform | Primary rule shift | Control shift | Secondary rule−control |
|---|---|---|---|
| original | +0.5014 [+0.1650, +0.9695], n=10 | +0.4965 [+0.1620, +0.9676], n=10 | +0.0049 [+0.0002, +0.0122], n=10 |
| renamed | +0.7378 [+0.2916, +1.2581], n=10 | +0.7076 [+0.2571, +1.2330], n=10 | +0.0302 [-0.0049, +0.0850], n=10 |

Positive rule shift means the early decoder readout moves toward d at whichever of P/Q the box rule forces. A similar positive control shift means solution-changing remote clues also produce appropriate directional sensitivity. The secondary difference tests a relative early advantage, not an internal mechanism. These endpoints must not be substituted for the original same-solution study result.

Renamed primary sign reversal: False. Missing engineering trajectories: []. Final Sudoku failures remain included.

Final valid-grid counts: {"original": {"rule_P": 10, "rule_Q": 10, "control_P": 9, "control_Q": 10}, "renamed": {"rule_P": 10, "rule_Q": 10, "control_P": 9, "control_Q": 10}}.
Pair stability: {"original": {"rule_P": {"mean_level": 9.8, "never_stable": 0}, "rule_Q": {"mean_level": 10.1, "never_stable": 0}, "control_P": {"mean_level": 10.2, "never_stable": 0}, "control_Q": {"mean_level": 10.4, "never_stable": 0}}, "renamed": {"rule_P": {"mean_level": 10.7, "never_stable": 0}, "rule_Q": {"mean_level": 10.8, "never_stable": 0}, "control_P": {"mean_level": 10.6, "never_stable": 0}, "control_Q": {"mean_level": 10.8, "never_stable": 0}}}.

Observed costs: {"trajectories": 80, "selected_planned_trajectories": 80, "median_board_seconds": 0.8447740499977954, "total_inference_seconds": 68.33757750020595, "peak_memory_bytes": 576966656, "cache_bytes": 6622473}.
Construction denominators: {"Target row/column also forces d": 47, "accepted_confirmation": 100, "accepted_pilot": 10, "candidates_attempted": 157, "fresh_source_families": 221, "geometry_eligible_candidates": 358, "no_eligible_quadruplet": 111, "no_valid_quadruplet": 47, "prior_or_engineering_family": 30, "removal_extra_solutions_rejected": 592, "removal_local_labels_rejected": 639, "selected_families": 110, "source_rows_scanned": 251, "total_source_rows": 2000}.

The four arms share a 34-clue scaffold with exactly two completions, then one same-digit clue selects each unique answer. Controls preserve both target cells’ local candidates and the target box’s d/e candidate positions. Row/column hidden-single alternatives at the forced location are excluded. Rule and control edit displacements and pooled band/stack relations match exactly. Necessary adjacency differences and residual center-distance/difficulty mismatches remain; balance.csv reports them. This selected connected-swap population differs from the original medium puzzles. Unknown Sudoku symmetries may remain beyond digit renaming and square dihedral grouping.

Reproduce the primary mean from family-analysis.csv: keep original complete families and average D_rule. No generator probabilities were recorded, no weights changed, and every inference used the full hierarchy.
