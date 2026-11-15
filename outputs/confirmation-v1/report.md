# Confirmation · hidden-single response



Status: complete.



Primary specificity: -0.0205 (95% percentile interval -0.0549, 0.0124; n=100).

Enabling A−B: -0.0198 (95% percentile interval -0.0538, 0.0112; n=100); control C−B: 0.0006 (95% percentile interval -0.0205, 0.0194; n=100).

Renamed specificity: -0.0019 (95% percentile interval -0.0306, 0.0291; n=100). Sign reversal: False.

Unaffected-cell specificity (one average per family): {'n': 100, 'mean': -0.015182267931571743, 'median': 0.0, 'fraction_positive': 0.13, 'ties': 73, 'ci95': [-0.03761600521424609, 0.001841674805764898], 'sd': 0.10224860846003354}.



Yield: 100 triplets from 253 scanned rows; 39.53 per 100.

Costs: {"completed_trajectories": 600, "planned_trajectories": 600, "median_board_seconds": 0.9108882500004256, "total_board_seconds": 560.1228472000512, "peak_process_memory_bytes": 576552960, "cache_bytes": 49681798}.

Precision planning: {"goal_half_width": 0.5, "observed_family_sd": 0.1693697050904791, "basis": "confirmation", "projected_n_for_goal": 1, "projected_half_width_at_100": 0.03319646219773391, "projected_600_trajectory_seconds": 546.5329500002554}.

Missing trajectories by arm: {}. Engineering failures are excluded as complete triplets, never scored as Sudoku failures.



Stability and ties: {"B": {"earlier": 4, "ties": 87, "later": 9}, "C": {"earlier": 6, "ties": 87, "later": 7}}.

Never-stable fractions and mean levels: {"A": {"mean_level": 9.86, "never_stable_fraction": 0.0}, "B": {"mean_level": 9.7, "never_stable_fraction": 0.0}, "C": {"mean_level": 9.86, "never_stable_fraction": 0.0}}.

Final valid counts: {'A': 94, 'B': 94, 'C': 95}. All complete traces enter the primary estimate, including final failures.

Closely matched subset: {'n': 18, 'mean': -0.05601860858775952, 'median': 0.0, 'fraction_positive': 0.0, 'ties': 14, 'ci95': [-0.13384200356624745, -0.0006401781682615009], 'sd': 0.16064371810718828}; criterion: same removal, equal target counts, geometry L1 <= 6.



This measures preference strength under selected clue edits. Stable full-vocabulary correctness is a separate endpoint. A positive A−C can arise from a decline in C; the A−B component must be read alongside it. Spatial controls, digit renaming and balance describe specificity; they cannot identify an internal deduction mechanism. Digit renaming and square dihedral duplicates are grouped; other unknown Sudoku automorphisms may remain. A wide or near-zero interval leaves the question open. No training or adaptive stopping was used.



Reproduce the estimate from family-analysis.csv: filter transform=original and missing=False; average specificity. The bootstrap resamples whole family rows, preserving arms and levels. All level curves are descriptive.
