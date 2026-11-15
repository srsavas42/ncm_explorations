# Hidden-single experiment · November 14, 2026

The implementation, worked fixture, ten-family pilot and frozen 100-family confirmation are complete. The confirmation does **not support the predicted positive early response** to the hidden-single enabling edit under this protocol. This is a behavioral result on the selected puzzle population, not a finding about the model's internal mechanism.

## Primary results

Margins are raw decoder score differences between the correct digit and its local rival, averaged over levels 1–6. Specificity is A−C. The intervals use 10,000 seeded bootstrap resamples of whole solved-grid families.

| Cohort / transform | Families | Enabling A−B | Control C−B | Specificity A−C | 95% specificity interval |
|---|---:|---:|---:|---:|---|
| Pilot / original | 10 | 0.0000 | +0.0794 | −0.0794 | [−0.2412, +0.0029] |
| Pilot / renamed | 10 paired repeats | −0.0204 | +0.0004 | −0.0208 | [−0.0627, +0.0003] |
| Confirmation / original | 100 | −0.0198 | +0.0006 | −0.0205 | [−0.0549, +0.0124] |
| Confirmation / renamed | 100 paired repeats | −0.0571 | −0.0551 | −0.0019 | [−0.0306, +0.0291] |

The confirmation primary median is zero: 73 exact ties, 11 positive effects and 16 negative effects. The interval includes zero. Renaming preserves the mean's sign but gives an estimate even closer to zero. The original-family enabling response is slightly negative, with its own interval spanning zero. These results provide no positive evidence for the proposed early preference gain.

## Fixture, yield and secondary results

- The worked r8c3 fixture passes every structural assertion, including 35 clues, unique shared solution, candidates {3,7}, frozen direct peers, correct moves and row/column exclusions. Its three early margin curves coincide. The figure includes all three actual trajectories; equal readouts overlap.
- The pilot selected 10 families from 106 scanned source rows, including 23 families assigned to its split: 9.43 selected triplets per 100 scanned rows.
- Confirmation selected 100 from 253 scanned rows, including 207 families assigned to its split: 39.53 per 100 scanned rows. The split fractions differ, so these raw yields have different denominators. Both scans used the same fixed selection rules.
- Confirmation target stability: A earlier than B in 4 families, tied in 87, later in 9; A earlier than C in 6, tied in 87, later in 7. All original target readouts were permanently correct by the final level.
- Original final valid-grid counts are A=94, B=94, C=95 out of 100. Renamed counts are A=97, B=93, C=98. Final failures remain in the analysis.
- Predetermined spatial controls were available in all 100 confirmation families. Their mean specificity was −0.0152, interval [−0.0376, +0.0018]; there is no clear target-specific positive gain.
- The predeclared closely matched subset has 18 original families, mean specificity −0.0560, interval [−0.1338, −0.0006]. This small secondary subset is descriptive and does not replace the full primary estimate.
- There were no missing or failed study trajectories. A/B-only search targets were counted (2 pilot, 4 confirmation) and excluded from paired inference; no descriptive model analysis of that material was run.

## Engineering checks and cost

All 27 tests pass. Both published independent parity examples match the generated code IDs and all 12 levels' tokens. Repeated readouts match exactly, and final outputs agree with an uninstrumented upstream run. All 81 coordinates and digit IDs round-trip. Corrupt/nonunique/contradictory boards are rejected as expected; permutation invariants and the synthetic signed-effect checks pass.

All selected source rows and edit endpoints rebuild the archived boards and pass exact solution checks. Pilot and confirmation families are disjoint. Repeating pilot preparation reproduces its manifest. A resumed pilot run reused all 60 complete traces with no new study inference and identical results. Recovery tests cover partial and truncated trace files and keep engineering errors distinct from Sudoku failures.

The main experiment comprises 663 saved study trajectories: 3 worked-fixture arms, 60 pilot trajectories and 600 confirmation trajectories, plus independent parity runs. Confirmation used CPU float32 and four intra-op threads. Median inference was 0.911 seconds per board; the 600 board traces took 560.1 seconds of measured inference and 618.6 seconds elapsed for the run, including setup, checks and writing. Peak process memory was 576.6 MB; confirmation trace storage was 49.7 MB. These are observed costs on this machine, not hardware-independent estimates.

Before confirmation inference, the count was frozen at 100, capped at 100, with a 2,000-row source budget, a 14,400-second compute budget and the unchanged levels 1–6 early window. The pilot forecast an interval half-width about 0.050 at n=100; the realized primary interval has half-width about 0.034, within the proposed 0.5-unit precision goal. The timestamped decision and pre-outcome analysis source hash are archived.

One reporting metadata correction followed inference: the generic field `pilot_sd` was renamed `observed_family_sd` and given a cohort label, because in the confirmation report it held confirmation SD. The frozen decision still records the actual pilot projection. The original analysis source, before/after hashes and equality checks are archived in `report-corrections.json`; every family-table entry and outcome statistic is unchanged.

## Read and reproduce

- [Worked fixture figure](outputs/fixture/fixture-margins.png)
- [Pilot report](outputs/pilot-v1/report.md) and [paired-effect figure](outputs/pilot-v1/cohort-effects.png)
- [Confirmation report](outputs/confirmation-v1/report.md), [paired-effect figure](outputs/confirmation-v1/cohort-effects.png), and [family table](outputs/confirmation-v1/family-analysis.csv)
- [Frozen confirmation decision](outputs/confirmation-v1/confirmation-decision.json), [source reconstruction audit](outputs/confirmation-v1/independent-audit.json), and [measurement details](docs/measurement.md)

```powershell
.venv\Scripts\python.exe scripts/reproduce_estimate.py outputs/confirmation-v1/family-analysis.csv
.venv\Scripts\python.exe -m ncm_probe report --config configs/confirm.toml
```

The first command independently reconstructs the point estimate and interval from the family table. The second rebuilds the report from saved traces without inference. Versions, hashes, environment, source selection, matching balance, per-level grid validity and missing-data accounting are preserved in the output directories. Model/data assets and raw trace caches are local and ignored by Git; the analysis tables, manifests and figures are available to track in the repository.

Digit renaming and square dihedral duplicates are grouped; other unknown Sudoku automorphisms may remain. The edits change evidence elsewhere in each puzzle and select a special puzzle population. A stronger claim about reasoning, a mechanism transplant, training or adaptive stopping would require a separate study. The present result calls first for examining readout sensitivity and the many exact early ties, rather than advancing a successful-deduction claim.
