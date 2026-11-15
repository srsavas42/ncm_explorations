# Opposite-answer follow-up · confirmation

Status: complete. The predeclared primary is the directional rule shift, with positive predicted. Intervals below are 95% percentile resamples of whole families.

| Transform | Primary rule shift | Control shift | Secondary rule−control |
|---|---|---|---|
| original | +0.8378 [+0.6857, +1.0094], n=100 | +0.7317 [+0.5727, +0.9113], n=100 | +0.1061 [+0.0435, +0.1749], n=100 |
| renamed | +0.8390 [+0.6682, +1.0263], n=100 | +0.8318 [+0.6558, +1.0235], n=100 | +0.0072 [-0.0845, +0.0829], n=100 |

Positive rule shift means the early decoder readout moves toward d at whichever of P/Q the box rule forces. A similar positive control shift means solution-changing remote clues also produce appropriate directional sensitivity. The secondary difference tests a relative early advantage, not an internal mechanism. These endpoints must not be substituted for the original same-solution study result.

Renamed primary sign reversal: False. Missing engineering trajectories: []. Final Sudoku failures remain included.

Final valid-grid counts: {"original": {"rule_P": 94, "rule_Q": 97, "control_P": 91, "control_Q": 93}, "renamed": {"rule_P": 92, "rule_Q": 95, "control_P": 95, "control_Q": 91}}.
Pair stability: {"original": {"rule_P": {"mean_level": 10.71, "never_stable": 0}, "rule_Q": {"mean_level": 10.7, "never_stable": 0}, "control_P": {"mean_level": 10.77, "never_stable": 4}, "control_Q": {"mean_level": 10.68, "never_stable": 2}}, "renamed": {"rule_P": {"mean_level": 10.38, "never_stable": 0}, "rule_Q": {"mean_level": 10.48, "never_stable": 0}, "control_P": {"mean_level": 10.73, "never_stable": 2}, "control_Q": {"mean_level": 10.4, "never_stable": 1}}}.

Observed costs: {"trajectories": 800, "selected_planned_trajectories": 800, "median_board_seconds": 0.8485640500002773, "total_inference_seconds": 691.9853851001244, "peak_memory_bytes": 576921600, "cache_bytes": 66211589}.
Construction denominators: {"Target row/column also forces d": 47, "accepted_confirmation": 100, "accepted_pilot": 10, "candidates_attempted": 157, "fresh_source_families": 221, "geometry_eligible_candidates": 358, "no_eligible_quadruplet": 111, "no_valid_quadruplet": 47, "prior_or_engineering_family": 30, "removal_extra_solutions_rejected": 592, "removal_local_labels_rejected": 639, "selected_families": 110, "source_rows_scanned": 251, "total_source_rows": 2000}.

The four arms share a 34-clue scaffold with exactly two completions, then one same-digit clue selects each unique answer. Controls preserve both target cells’ local candidates and the target box’s d/e candidate positions. Row/column hidden-single alternatives at the forced location are excluded. Rule and control edit displacements and pooled band/stack relations match exactly. Necessary adjacency differences and residual center-distance/difficulty mismatches remain; balance.csv reports them. This selected connected-swap population differs from the original medium puzzles. Unknown Sudoku symmetries may remain beyond digit renaming and square dihedral grouping.

Reproduce the primary mean from family-analysis.csv: keep original complete families and average D_rule. No generator probabilities were recorded, no weights changed, and every inference used the full hierarchy.
