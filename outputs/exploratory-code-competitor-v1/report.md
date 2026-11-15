# Exploratory code and competitor check

These checks reuse existing traces after inspecting the primary results. They do not change the frozen target-cell primary endpoint and are not an independent confirmation of a competitor hypothesis.

## Worked fixture

A, B and C have identical code prefixes through level 7 and identical full decoder scores across every cell through those levels. A first differs from B at level 8 (one of 26 code positions). C first differs from B at level 10. The early A−B and C−B changes are exactly zero at both target and competitor.

All arms first select 7 at the target at level 4, switch to 1 at levels 7–8, and remain correct from level 9 onward. A third digit did not give A an earlier selection advantage.

At the first A/B divergence, the competitor’s raw score for 7 increases by about 0.046 in A. This is not the proposed raw-score drop. Later changes vary in direction. The full-vocabulary probability and true-digit-versus-7 margin are also saved, because raw logits can shift together.

Code-selection probabilities were not stored. Decoder logits are saved, but they describe different predictions and cannot be used as code-selection probabilities. Inspecting subtler generator responses would require a new, separately logged instrumented replay.

## Existing cohorts (exploratory)

| Cohort / transform | A/B prefixes identical through 6 | Both readouts change | Target only | Competitor only | Neither |
|---|---:|---:|---:|---:|---:|
| pilot-v1 / original | 10/10 | 0 | 0 | 0 | 10 |
| pilot-v1 / renamed | 8/10 | 2 | 0 | 0 | 8 |
| confirmation-v1 / original | 72/100 | 28 | 0 | 0 | 72 |
| confirmation-v1 / renamed | 75/100 | 25 | 0 | 0 | 75 |

A change means any nonzero level-wise change in the early window, regardless of direction. Different selected codes or a shifted readout do not identify use of a hidden-single rule.

| Cohort / original | A−B competitor elimination margin | C−B competitor elimination margin | A−C competitor elimination margin |
|---|---|---|---|
| pilot-v1 | +0.0000 [+0.0000, +0.0000] | -0.0147 [-0.0420, +0.0000] | +0.0147 [+0.0000, +0.0420] |
| confirmation-v1 | +0.0065 [-0.0335, +0.0493] | -0.0132 [-0.0386, +0.0045] | +0.0197 [-0.0121, +0.0577] |

Values are means with exploratory 95% family bootstrap intervals. Positive means stronger preference for the competitor’s actual solution digit over the ruled-out digit. A−B and C−B are shown separately so a control-edit effect cannot masquerade as an enabling effect. Renamed effects and probability changes are in analysis.json.

The output tables include all 12 levels, all three pair comparisons, original and renamed families, and exact prefix equality. The next inferential test should define competitor endpoints before looking at fresh puzzle outcomes.
