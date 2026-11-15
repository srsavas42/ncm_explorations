# Opposite-answer follow-up · protocol v1

This is a separate behavioral hypothesis. The original experiment and its frozen primary result stand on their own. No model outcomes are used to choose puzzles, locations, edits or matching. This protocol is written before running this follow-up's model trajectories.

## Prediction and endpoints

Two fixed cells P and Q in one box exchange digits d and e between two valid completed grids. Every rule/control arm is uniquely solvable. P is the lower zero-based cell index; no model outcome determines its label. For each generated level define an assignment preference:

`q(X,k) = 0.5 * [(z(X,k,P,d) - z(X,k,P,e)) - (z(X,k,Q,d) - z(X,k,Q,e))]`.

Each difference compares digits at the same cell, avoiding arbitrary offsets between cells' raw logits. Positive q favors d at P and e at Q; negative q favors the opposite assignment. Average equally over one-based levels 1–6, fixed in advance.

**Primary directional endpoint:** `D_rule = mean_early(q(rule_P)) - mean_early(q(rule_Q))`. The predeclared prediction is positive: early preference shifts toward whichever location the box rule forces. Report mean, median, positive fraction, exact ties and a 95% percentile interval from 10,000 seeded whole-family bootstrap draws. This measures responsiveness to the forced answer, not a mechanism.

**Control endpoint:** `D_control = mean_early(q(control_P)) - mean_early(q(control_Q))`, with the same two corresponding solutions and an expected positive direction for appropriate answer sensitivity. Report it separately. **Secondary specificity endpoint:** `D_rule - D_control`. A positive primary alone does not establish a benefit specific to the box deduction. Do not change the primary to the interaction after viewing results.

Secondary readouts include full-vocabulary target winners, the earliest level where both cells' correct assignment remains stable through level 12 (13 if never), final grid validity, accuracy on the changed component, and selected-code first divergence. Read all 12 levels. Retain final Sudoku failures; list engineering failures separately. No adaptive stopping or training.

## Construction

Start from released solutions not used in the prior study. For each pair of digits, connect their occurrences when they share a row, column or box. Swapping d/e on a connected component preserves Sudoku constraints. Allow component sizes 6, 8, 10, 12 or 14; exclude 4-cell rectangles because they cannot provide a remote solution-changing control, and exclude a global 18-cell digit rename.

Select two component cells P/Q in one box. Build a common 34-clue scaffold that has **exactly two completions**, verified by counting up to three and checking both against the specified grids. Both P and Q have local candidates {d,e}; the box has exactly these two possible locations for each of d and e. The scaffold is intentionally ambiguous and is not a scored inference arm.

Build four 35-clue puzzles, each adding one clue of the same digit d to that same scaffold:

- `rule_P`: reveal d at a component cell outside the target box that is a peer of Q and not P. The target box then forces d at P.
- `rule_Q`: the opposite solution, with d at a peer of P and not Q, forcing d at Q.
- `control_P`: reveal d at a differing component cell outside the peers of **both** P and Q, selecting the P solution while leaving the initial target-box d/e candidate positions unchanged.
- `control_Q`: the corresponding remote reveal selecting the Q solution, again leaving both locations available initially in the target box.

All four arms have the same clue count, digit frequencies and common clue scaffold. Exact-check each arm for its distinct intended unique completion. In rule arms, the forced cell must still have {d,e}, so it is not a naked single. In every arm exclude a hidden single for d in the forced cell's row or column. Controls preserve both {d,e} local sets and both d/e box-location sets; they create neither of those named box deductions in the target box. Other deductions elsewhere may exist and are logged as initial forced-cell proxies.

## Geometry matching

Require **exact matching** of the absolute row and column displacement between the rule edit endpoints and between the control edit endpoints. Also require the same pooled counts of endpoints in the target box's band and stack. Rank survivors first by the L1 mismatch in absolute distances from the target-box center, then by the sum of differences in initially forced-cell counts between corresponding rule/control arms; break ties with the fixed seed. Archive the full geometry and all mismatch components.

This is not perfect causal isolation: a rule clue must adjoin the eliminated cell, whereas a remote control must avoid both cells' peers. That adjacency difference is necessary to the intervention and cannot be matched away. Residual geometry mismatches are reported rather than concealed or called exact. The four completed puzzles may differ from the original medium difficulty distribution.

## Freshness, selection and budgets

Exclude the prior fixture, all prior scanned source families (not merely the selected 110), source rows 0 and 1 used for independent parity, and either completed-grid family of any previously selected new quadruplet. Group solutions using the existing digit-renaming and eight square-dihedral canonicalization; other unknown Sudoku automorphisms are not exhaustively detected. Reject candidates whose alternate completion matches an excluded family.

Also exclude source rows 300–329, used for model-blind construction engineering, from both study splits. The committed engineering fixture uses source row 300 and is outside both samples. Its model readout is used only to validate the new plotting/reporting path.

The fixed config seeds source order, target/component order, deletion order and digit permutations. Start from all clues shared by the two completions and greedily remove clues while preserving exactly those two solutions and the target labels. Allow three deletion orders per candidate, at most 32 geometric candidates per source and at most 2,000 source rows. Choose the first qualifying target/component in shuffled order, then the documented endpoint rank. Every family contributes once. Retain rejection and yield denominators.

Freeze up to ten pilot families and the next 100 independent confirmation families in the same preparation, before inspecting any model trace. Keep both solution-family keys reserved across splits. Apply one seeded nonidentity digit permutation consistently to each family; repeats are robustness runs and do not increase n. Eight trajectories per family: four original, four renamed. A complete pilot is 80 trajectories; confirmation is 800. Fixed CPU inference budget is 14,400 seconds per invocation, with cached engineering resumes. If construction falls short, report feasibility at the actual n and retain the source budget; do not relax labels after seeing outcomes.

Use the same pinned frozen model, CPU float32, four threads, deterministic greedy generation, full cumulative readout, vocabulary mapping and independent parity gates. Keep the model adapter unchanged. Record protocol and manifest hashes, revisions, all source and construction provenance, and the selected sample before inference. Reports are rebuilt from saved traces. Confirmation decisions and status are reported separately from the pilot.
