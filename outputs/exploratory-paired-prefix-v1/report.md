# Paired prefix sensitivity · exploratory

The frozen confirmation primary A−C estimate is -0.0205, 95% family bootstrap interval [-0.0549, 0.0124] (n=100). It does not support the predicted positive early target preference. This remains the primary result.

The following analysis was requested after observing those outcomes. It reuses saved traces, runs no inference, and does not modify the frozen primary analysis.

## Paired counts through level 6 · 100 original confirmation families

| Prefix differs from B | Families |
|---|---:|
| Neither edit | 64 |
| Only A | 13 |
| Only C | 8 |
| Both | 15 |

A differs from B in 28 families; C differs from B in 23. These are paired observations, not independent samples. Earlier code divergence measures sensitivity to a clue edit, not whether its consequence is expressed in the predicted direction.

## First selected-code divergence from B

| Level | A versus B | C versus B |
|---|---:|---:|
| 1 | 9 | 4 |
| 2 | 1 | 0 |
| 3 | 5 | 5 |
| 4 | 6 | 5 |
| 5 | 0 | 0 |
| 6 | 7 | 9 |
| 7 | 10 | 10 |
| 8 | 16 | 12 |
| 9 | 14 | 18 |
| 10 | 7 | 11 |
| 11 | 10 | 10 |
| 12 | 2 | 0 |
| never | 13 | 16 |

A diverges earlier in 35 families, C earlier in 22, and first-divergence times tie in 43. For this descriptive comparison, no divergence through level 12 is treated as level 13. Equal first-divergence times do not imply equal selected prefixes.

## Relation to the primary estimate

| Level-6 group | n | A/C prefixes identical | Mean A−C target margin | Contribution to overall mean |
|---|---:|---:|---:|---:|
| neither | 64 | 64 | +0.000000 | +0.000000 |
| only_A | 13 | 0 | -0.089459 | -0.011630 |
| only_C | 8 | 0 | +0.065137 | +0.005211 |
| both | 15 | 9 | -0.093750 | -0.014063 |

In 9 of the 15 families where both edits change the prefix, A and C select the same changed prefix. Their primary contrast is therefore zero. The 72 unchanged A/B prefixes alone cannot establish the A−C result: C changes in the only-C group, and other groups can contribute effects of either sign. Group contributions sum to the unchanged full-cohort estimate.

The existing target/competitor readout directions remain the relevant check on resemblance to the deduction. The separately reported exploratory competitor interval spans zero. These descriptive prefix counts do not resolve that direction. No code-selection probabilities were collected or inferred from decoder scores.

All 12 paired cumulative counts, pilot results and renamed repeats are available in analysis.json and the CSV tables. Original families remain primary; renamed repeats do not increase the independent sample size.
