# Pilot · hidden-single response



Status: complete.



Primary specificity: -0.0794 (95% percentile interval -0.2412, 0.0029; n=10).

Enabling A−B: 0.0000 (95% percentile interval 0.0000, 0.0000; n=10); control C−B: 0.0794 (95% percentile interval -0.0029, 0.2412; n=10).

Renamed specificity: -0.0208 (95% percentile interval -0.0627, 0.0003; n=10). Sign reversal: False.

Unaffected-cell specificity (one average per family): {'n': 10, 'mean': 0.00922443637003501, 'median': 0.0, 'fraction_positive': 0.2, 'ties': 8, 'ci95': [0.0, 0.024073291880389053], 'sd': 0.023535584375560956}.



Yield: 10 triplets from 106 scanned rows; 9.43 per 100.

Costs: {"completed_trajectories": 60, "planned_trajectories": 60, "median_board_seconds": 0.9070412000000942, "total_board_seconds": 54.87884219994885, "peak_process_memory_bytes": 575287296, "cache_bytes": 4968885}.

Precision planning: {"goal_half_width": 0.5, "observed_family_sd": 0.2546022808782507, "basis": "pilot", "projected_n_for_goal": 1, "projected_half_width_at_100": 0.04990204705213714, "projected_600_trajectory_seconds": 544.2247200000565}.

Missing trajectories by arm: {}. Engineering failures are excluded as complete triplets, never scored as Sudoku failures.



Stability and ties: {"B": {"earlier": 0, "ties": 10, "later": 0}, "C": {"earlier": 2, "ties": 7, "later": 1}}.

Never-stable fractions and mean levels: {"A": {"mean_level": 10.6, "never_stable_fraction": 0.0}, "B": {"mean_level": 10.6, "never_stable_fraction": 0.0}, "C": {"mean_level": 10.7, "never_stable_fraction": 0.0}}.

Final valid counts: {'A': 10, 'B': 10, 'C': 10}. All complete traces enter the primary estimate, including final failures.

Closely matched subset: {'n': 2, 'mean': 0.0, 'median': 0.0, 'fraction_positive': 0.0, 'ties': 2, 'ci95': [0.0, 0.0], 'sd': 0.0}; criterion: same removal, equal target counts, geometry L1 <= 6.



This measures preference strength under selected clue edits. Stable full-vocabulary correctness is a separate endpoint. A positive A−C can arise from a decline in C; the A−B component must be read alongside it. Spatial controls, digit renaming and balance describe specificity; they cannot identify an internal deduction mechanism. Digit renaming and square dihedral duplicates are grouped; other unknown Sudoku automorphisms may remain. A wide or near-zero interval leaves the question open. No training or adaptive stopping was used.



Reproduce the estimate from family-analysis.csv: filter transform=original and missing=False; average specificity. The bootstrap resamples whole family rows, preserving arms and levels. All level curves are descriptive.
