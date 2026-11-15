# Opposite-answer follow-up · November 14, 2026

The predeclared directional prediction is supported on the 100-family confirmation sample: **early preference shifts toward whichever assignment the box rule forces**. Solution-changing remote controls also produce a positive shift. The additional rule-over-control advantage is positive on the original digit labels but is not clearly reproduced after digit renaming. This is evidence of directional answer sensitivity on the selected population, not identification of a hidden-single mechanism.

This is a separate experiment. The original same-solution result remains unchanged: its primary A−C estimate was −0.0205, with a 95% interval [−0.0549, +0.0124]. No original manifest, table, trace index or primary analysis was rewritten. The new endpoint has a different definition; these numerical effect sizes are not directly interchangeable.

## Predeclared endpoint and results

P and Q are two fixed blank cells in one box. The two possible completed grids swap digits d/e there. Positive assignment preference means d at P and e at Q; negative means the opposite. The readout averages the two same-cell digit-logit contrasts, avoiding arbitrary between-cell score offsets. Average over levels 1–6, fixed before inference.

The **primary** is the early preference in `rule_P` minus that in `rule_Q`, predicted positive. The control shift uses `control_P` minus `control_Q`. Their difference is **secondary**, and is not promoted to primary after observing outcomes. Intervals use 10,000 seeded resamples of whole solved-grid families.

| Cohort / transform | Families | Primary rule shift [95% interval] | Control shift [95% interval] | Secondary rule−control [95% interval] |
|---|---:|---|---|---|
| Pilot / original | 10 | +0.5014 [+0.1650, +0.9695] | +0.4965 [+0.1620, +0.9676] | +0.0049 [+0.0002, +0.0122] |
| Pilot / renamed | 10 paired repeats | +0.7378 [+0.2916, +1.2581] | +0.7076 [+0.2571, +1.2330] | +0.0302 [−0.0049, +0.0850] |
| Confirmation / original | 100 | +0.8378 [+0.6857, +1.0094] | +0.7317 [+0.5727, +0.9113] | +0.1061 [+0.0435, +0.1749] |
| Confirmation / renamed | 100 paired repeats | +0.8390 [+0.6682, +1.0263] | +0.8318 [+0.6558, +1.0235] | +0.0072 [−0.0845, +0.0829] |

In the original confirmation families, 96/100 primary shifts are positive; the median is +0.6256, with no exact ties. The controls are positive in 89/100 families. After renaming, primary shifts are positive in 87/100 families and controls in 85/100. These are preference-strength endpoints, not a guarantee that the correct digits are the full-vocabulary winners at an early level.

The secondary original-label contrast has median zero: 39 positive, 26 negative and 35 exact ties. Its positive mean and interval should be reported, alongside the renamed estimate whose interval spans zero. The difference in interval inclusion by itself is not a formal test of a digit-label interaction. The extra advantage for the box rule is not robustly established across the two labelings.

## What was constructed

Each family has a **34-clue common scaffold with exactly two completions**, checked by counting up to three and matching the specified pair of solutions. Four puzzles add one clue of the same digit d:

- `rule_P` and `rule_Q` expose box hidden singles forcing opposite locations.
- `control_P` and `control_Q` use remote clues to select the same respective solutions while leaving the target box's entire initial candidate sets unchanged.

All four arms have 35 clues, the same digit counts and individually verified unique solutions. The rule-forced cell retains two local candidates, and row/column hidden-single alternatives for d at that cell are excluded. Controls preserve both target cells' local candidates and both d/e box-location sets. The ambiguous scaffold is not an inference arm.

The two completed grids differ by a valid connected swap of two digits. Four-cell trades and whole-grid digit renames are excluded. Of the 100 confirmation families, 88 use 14-cell trades, nine use 12-cell trades and three use 10-cell trades. This concentration is a limitation of the selected construction population.

Edit matching is exact for clue count, digit counts, absolute row/column displacement between the two rule endpoints versus the two control endpoints, and pooled band/stack relation to the target box. Residual distance-to-box-center L1 mismatch has median 4 and range 0–22. Required adjacency to the eliminated cell differs from the remote controls by design; geometry is not perfectly isolated. All raw geometry, difficulty proxies and mismatches are in each split's balance.csv and the family manifest.

Preparation found 110 eligible families from 251 scanned source rows: 221 fresh source families were examined and 30 prior/engineering families skipped. The exclusion set has 283 family keys, covering prior scanned families, parity inputs and construction-engineering rows. Both solution-family keys are reserved for every selected family: 220 distinct keys across ten pilot and 100 confirmation families. Known digit-renamed and square-dihedral duplicates are grouped. Unknown additional Sudoku symmetries may remain. Freshness here is relative to this project's earlier study, not an assertion about the model's training data.

Both splits and all permutations were frozen together before model traces were inspected. Repeating preparation reproduces the manifest. The timestamped confirmation decision retained the already-reserved 100 families and unchanged endpoint after observing feasible pilot CPU latency.

## Secondary readouts and execution

All 100 original confirmation rule-answer pairs have differing selected code prefixes by level 6, as do all 100 control-answer pairs. The same holds after digit renaming. Conversely, same-answer rule/control prefixes match through level 6 in 55/100 P arms and 63/100 Q arms (57 and 59 after renaming). These selected-code comparisons are secondary; no generator choice probabilities were collected.

Original final valid-grid counts are rule_P=94, rule_Q=97, control_P=91, control_Q=93. Renamed counts are 92, 95, 95 and 91 respectively. All final failures remain in the primary analysis. Original rule arms had no never-stable target pairs; controls had four P and two Q pairs that never became permanently correct. Per-level full-vocabulary winners, component accuracy and grid checks are saved.

There are **888 completed study trajectories**: eight engineering-fixture trajectories, 80 pilot trajectories and 800 confirmation trajectories, plus independent parity checks. There were no engineering failures or missing study traces. The same unchanged frozen adapter, weights, CPU float32, four threads and deterministic full-hierarchy decoding were used. Generator probabilities, training and adaptive stopping were deferred.

Confirmation median inference time was 0.849 seconds per board, with 692.0 seconds of summed inference and 735.3 seconds elapsed for the run. Peak process memory was 576.9 MB, and confirmation trace storage was 66.2 MB. These are observed costs on this machine, not general hardware benchmarks.

All **42 tests pass** in the Desktop installation. Both independent release parity fixtures match. All 110 quadruplets and their digit renamings pass structural audits. The full target-box candidate sets are unchanged in all 220 original control boards. The installed pilot resumes with 80 cache hits and zero new study inference. An independent CSV reconstruction reproduces every pilot/confirmation mean, median, positive fraction, tie count and interval for all three effects under both labelings. The pre-outcome analysis source hash is unchanged.

## Artifacts and reproduction

- [Predeclared protocol](docs/opposite-protocol.md) and [frozen protocol/manifest](outputs/opposite-v1/protocol.json)
- [Four-board fixture illustration](outputs/opposite-v1/fixture/opposite-boards.png) and [fixture readouts](outputs/opposite-v1/fixture/opposite-effects.png)
- [Pilot report](outputs/opposite-v1/pilot/report.md)
- [Confirmation report](outputs/opposite-v1/confirmation/report.md), [figure](outputs/opposite-v1/confirmation/opposite-effects.png), and [family table](outputs/opposite-v1/confirmation/family-analysis.csv)
- [Structural audit](outputs/opposite-v1/structural-audit.json), [confirmation decision](outputs/opposite-v1/confirmation-decision.json), and [independent reconstruction](outputs/opposite-v1/estimate-reconstruction-audit.json)

```powershell
.venv\Scripts\python.exe scripts/reproduce_opposite_estimate.py outputs/opposite-v1/confirmation/family-analysis.csv
.venv\Scripts\python.exe -m ncm_probe.opposite report --config configs/opposite.toml --split confirmation
.venv\Scripts\python.exe -m scripts.opposite_code_summary --split confirmation
```

These commands analyze saved artifacts and do not rerun inference. The first experiment answers whether making an existing answer easier strengthens its early readout; this follow-up answers whether early readout tracks an answer that actually changes. The positive new directional result and the original null result can both hold.
