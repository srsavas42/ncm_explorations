# Does NCM respond to a hidden single?
## Implementation packet for a frozen-checkpoint Sudoku experiment

**Decision to make.** When one clue makes a named deduction immediately available, does the model favor the implied digit earlier in generation? The first study measures this behavior. Its strongest outcome would justify testing where the information is carried inside the model.

**First deliverable.** Produce one reproducible three-line plot for the verified example in §2. Then automate the same comparison over independent solved grids. A null, negative, or inconclusive result is a valid delivery. No NCM inference results or hardware timings are supplied in this packet.

**Resources.** Python, CPU-first, personal equipment and public assets only. Allow roughly five hands-on hours per week. Start with the released medium Sudoku tokenizer and generator and 35-clue boards. This is a design choice for this study. It matches the worked pair and the paper’s medium clue count. The edits create a selected puzzle population whose difficulty can differ from the original medium split. For the protocol below, keep the weights fixed and run the full hierarchy. Adaptive stopping and model training are separate studies.

### 1. Hypothesis and comparison

Use one rule, a **box hidden single**. For a digit d, check each empty cell of a 3×3 box against its visible row, column and box clues. If exactly one cell can contain d, that cell must contain it. A cell can have two locally legal digits while the box forces one of them. Compute these labels from the *initial clues*, before applying any deductions.

Choose a target cell t and its true digit d. Construct three puzzles from one completed solution.

| Board | How to obtain it | Eligible squares for d in the target box |
|---|---|---|
| B, common starting board | A uniquely solvable 35-clue puzzle | Exactly two, t and a competitor u |
| A, deduction available | Move one given d so that u is eliminated | Exactly one, t |
| C, control edit | Starting again from B, move one given d while leaving the box deduction unavailable | Exactly the same two as B |

The pair A/B measures the response to the enabling edit. C/B measures the response to another edit of the same digit. Comparing the two helps distinguish specific sensitivity from a general response to changed clues. This design controls the correct answer and the target’s immediate candidates. An edit also changes the evidence elsewhere on the board. Even an effect unique to A can have several computational explanations.

**Prediction.** Across held-out solution families, the early decoder score for d relative to its local alternative increases more after the enabling edit than after the control edit. A second, distinct question is whether d becomes and stays the highest-scoring output earlier. Score both. A greater early margin alone supports a claim about preference strength.

### 2. Verified fixture

Rows and columns below are one-based. A period is a blank. Each column of the table is a complete 81-cell test input when its nine strings are concatenated. The last column is reserved for the solver and the evaluator.

| Row | A • available | B • starting board | C • control | Shared solution |
|---|---|---|---|---|
| 1 | `...6.89..` | `...6.89..` | `...6789..` | `534678912` |
| 2 | `...195...` | `.7.195...` | `.7.195...` | `672195348` |
| 3 | `...34256.` | `...34256.` | `...34256.` | `198342567` |
| 4 | `.597..4.3` | `.597..4.3` | `.59...4.3` | `859761423` |
| 5 | `..6...7.1` | `..6...7.1` | `..6...7.1` | `426853791` |
| 6 | `71....85.` | `71....85.` | `71....85.` | `713924856` |
| 7 | `.....72.4` | `......2.4` | `......2.4` | `961537284` |
| 8 | `28.4196..` | `28.4196..` | `28.4196..` | `287419635` |
| 9 | `.45.8....` | `.45.8....` | `.45.8....` | `345286179` |

Expected assertions, checked with a backtracking solution counter:

- All three boards contain 35 clues, share the displayed unique solution, and leave **r8c3** blank with candidates **{3,7}**. Digit 7 is a hidden single in the target box only in A. It is not a hidden single in the target row or column in any arm.
- In B and C, the box permits 7 at **r7c3** and **r8c3**. In A, the given 7 at r7c6 eliminates r7c3. The only place left is r8c3.
- B → A moves the 7 at r2c2 to r7c6. B → C moves the 7 at r4c4 to r1c5. Exactly two positions change in each comparison. Every clue immediately adjoining t by row, column or box is identical across the three boards.
- The fixture illustrates an imperfect match worth logging. The target column has more legal locations for 7 in A than in B; the column cannot itself force the target in either board. Target-row and target-column candidate counts and edit geometry belong in the balance report.
- With a rule-based oracle scoring “the target is a box hidden single for 7” as 1, the fixture yields A=1, B=0, C=0. A baseline that sees only the target cell’s immediate candidate set must give identical scores across arms. These are software acceptance checks; the model’s response is an open question.

### 3. Inputs and model instrumentation

Use the public upstream code and medium files. Record the resolved commit for each repository, source filename, SHA-256 of downloaded inputs, license, Python/dependency versions, CPU, thread count, precision and decode configuration. Cache assets once. Keep the model adapter separate from the puzzle generator so that it accepts puzzle clues alone.

| Component | Public source and use |
|---|---|
| Model and generation code | [HazyResearch/ncm](https://github.com/HazyResearch/ncm). Start from its released Sudoku evaluation path and reuse its prefix construction, attention masks, code selection and tokenizer decoder. The README recommends CUDA. Verify a single-board CPU path before estimating throughput. |
| Frozen weights | [hazyresearch/ncm-checkpoints, sudoku/medium](https://huggingface.co/hazyresearch/ncm-checkpoints/tree/main/sudoku/medium). Fetch config.yaml, generator.pt and tokenizer.pt from one revision. The repository lists MIT. |
| Source boards | [hazyresearch/ncm-datasets, sudoku/medium](https://huggingface.co/datasets/hazyresearch/ncm-datasets/tree/main/sudoku/medium). Read puzzles.pickle and solutions.pickle from the released revision. Preserve row IDs. The repository lists MIT. Keep edited variants and source rows distinguishable. |
| Independent parity fixture | [mrfakename/ncm-webgpu-weights](https://huggingface.co/mrfakename/ncm-webgpu-weights). The sudoku-medium export documents PyTorch fixtures, code IDs and per-level decoded tokens. Use its matching metadata for token mapping and parity if helpful. The documented Sudoku outputs do not promise digit logits. |
| Methods | [NCM paper, §§3, 4.4 and Appendix J.7](https://arxiv.org/html/2610.14162v1) and [hidden-single definition](https://hodoku.sourceforge.net/en/tech_singles.php). |

**Measurement contract.** For each generated level, read the cumulative latent reconstruction after adding that level. Run it through the frozen tokenizer decoder and tap the output *before token argmax*. Save the decoder’s raw scores for digits 1–9 at all 81 cells and the top token over the full output vocabulary. Codebook selection logits describe a different prediction and cannot substitute for cell-digit logits. A special-token winner on a board cell is a cell-level miss. Preserve it when checking validity. Never overwrite predictions with original clues for scoring; record separately if the upstream pipeline enforces clues internally.

1. Load the matching upstream config, use evaluation mode, no gradients and fixed deterministic greedy decoding. Record every override. Prefer CPU float32 with fixed thread count. Run the reference input twice. Check final tokens against the release fixture or uninstrumented reference under identical settings. Compare all available intermediate tokens and code IDs. Resolve any mismatch before interpreting a trace.
2. Establish the mapping from 81 board coordinates to actual target token offsets and from digits to vocabulary IDs. Round-trip all 81 coordinates on a known solution including boundary cells. The model sequence can contain separators, padding and special tokens. Identify them from the pinned implementation.
3. Verify shape [K,81,9], finite scores, correct level order, vocabulary mapping and agreement between stored full-vocabulary winners and the reference token decoding. Compare the final instrumented run with instrumentation disabled. Reading intermediates must leave generation unchanged.
4. If the ONNX path returns only IDs, use the upstream decoder with the returned codes plus per-level reconstruction operators, or instrument PyTorch directly. Validate parity again. A hard-label plot can exercise the pilot pipeline while score extraction is pending. A missing score blocks the primary analysis; it must never be replaced with a one-hot pseudo-logit.
5. Optional low-cost readout control: teacher-encode the known solution and decode each partial reconstruction. With the same solution and deterministic tokenizer, the reference track is identical across A/B/C. It shows how readable this target is at each level when the encoder has the solution. Keep it out of generation and out of the primary response statistic.

### 4. Generate a cohort without selecting for model behavior

**Sampling unit.** One underlying completed grid, one triplet, one target per family. Start with the public medium boards in seeded shuffled order. Deduplicate source solutions and group digit-renamed duplicates by a first-occurrence canonicalization of the completed grid. Keep all generated variants from each family in one split. Keep any other known symmetry-related source duplicates together. Archive the one-off fixture separately from both pilot and confirmation.

**Construction algorithm.**

1. Validate the source clues and the supplied solution independently. Use a solver that counts completions up to two and rejects conflicting givens. Treat a qualified source as B, or search backwards from a source A for an eligible B. Predeclare which search directions are allowed and log source role. All variants must solve uniquely to the supplied grid.
2. Enumerate blank targets with exactly two local candidates {d,e}, where d is the solution digit. In B require exactly two legal d positions in the target box. Neither the row nor column of t may force d. Freeze the direct peer clues of t for all variants. This equalizes all local evidence visible from the target’s own row, column and box.
3. To propose a move from B, remove a clue d and reveal a previously blank d from the same solution. Both edit endpoints must be outside the target’s peers and differ from t. Keep the number of givens and the frequency of every digit constant. Recompute candidates on the edited board. Retain A moves yielding only t in the box and C moves preserving exactly the original two positions. Recheck target row/column hidden-single exclusions in every arm.
4. Exact-check survivors for uniqueness and solution identity. Store the target, rival, competitor, candidate masks, source/edit endpoints and which given excludes the competitor. The solutions and these rule labels are available only to preprocessing and evaluation. Reject all ill-formed variants with a reason.
5. Prefer a C edit with the same removed clue as A when feasible. Then minimize differences between A and C in geometric relation of edit endpoints to t, target row/column candidate counts for d, and number of initially forced cells elsewhere. Implement a documented lexicographic ranking, with seeded tie-breaking; store the component mismatches. Do not require an exact match on quantities the intervention must change. Choose targets and arm variants without reading model outputs.
6. Each qualifying family contributes once. Log source rows scanned, unique families, eligible A/B pairs, eligible triplets, rejection counts, candidate target distribution, geometry and matching quality. Keep these denominators even when the search yields little. Reserve A/B-only material for a labeled descriptive analysis.
7. For digit symmetry, draw one seeded nonidentity bijection per family on digits 1–9 and apply it consistently to all three arms, the correct digit and rival. Keep blanks and locations fixed. Verify inverse-map round trips and invariant solver labels. Treat renamed runs as paired repeats. Use originals for the primary estimate and the renamed triplets for robustness. If the effect changes sign, report it.

**Feasibility sequence.** Begin with the fixture, then target 10 independent pilot triplets. Measure eligible families per 100 source rows, median inference time per board, peak memory and storage. At six trajectories per family (three original, three renamed), 10 pilot families require 60 and 100 confirmation families require 600. Estimate compute from measured latency plus search and analysis time. Choose the confirmation count before viewing confirmation outcomes. An initial target of 100 eligible families is a planning value. Use the pilot SD of the family contrast to project a 95% interval half-width near 1.96 × SD / √n. Set a useful precision goal, fixed source/search budget and sample cap in the frozen config. If the cohort cannot reach that precision, report a feasibility or exploratory study and its interval. Do not search for more puzzles conditional on the observed model effect.

### 5. Primary endpoint, controls and analysis

Let z(X,k,t,j) be the *decoder* logit for digit j at the target after level k on board X. Let d be correct and e the other initially legal digit. Define the margin m(X,k) = z(X,k,t,d) − z(X,k,t,e). It is a log odds between the two tokens. Larger means stronger relative preference for the correct digit. It does not imply that d outranks all vocabulary tokens.

**Primary endpoint.** For a 12-level release, use one-based levels 1–6 as the proposed early window and average the margins equally across those levels. Confirm K from the checkpoint. Retain this default unless pilot engineering reveals a substantive measurement issue; document any revision before confirmation. Call the early averages M(A), M(B), M(C). For each family record:

- **Enabling response:** M(A) − M(B).
- **Control response:** M(C) − M(B).
- **Specificity contrast (primary):** [M(A) − M(B)] − [M(C) − M(B)] = M(A) − M(C). Positive favors the deduction condition. Report both component responses so that a control-induced decline cannot masquerade as stronger support under A.

Average the primary contrast over original held-out families. Report n, mean, median, fraction positive, exact ties and a 95% percentile interval from 10,000 seeded bootstrap draws of whole families with replacement. Preserve all arms and levels together. Provide the same signed effects on renamed families separately. Display all level-wise curves descriptively; do not choose the peak afterward. Use every complete trace regardless of final solve status. Resume engineering failures; if any remain, give their counts and causes by arm and use complete triplets for the paired estimate. Never count an inference error as a Sudoku failure.

**Secondary measures.**

- For each arm, earliest level after which the full-vocabulary top token at t is d through the final level; assign K+1 if never stable. Also report the never-stable fraction. Compare A/B and A/C, including ties. Early guesses and permanently correct readouts answer different questions.
- Track full-grid validity (digits 1–9, clues, every row/column/box), candidate-rule violations and blank-cell accuracy by level. Include final failures. For a spatial control, evaluate predetermined non-target cells blank in all arms with unchanged local candidate sets and unchanged hidden-single labels for their own correct digit. Prefer two-candidate cells so the same margin is defined. Summarize once per family; report coverage if none qualify. A similar change everywhere weakens specificity.
- Report target digits, box locations, edit geometry, candidate counts and whole-board difficulty proxies by arm. Inspect whether the result survives the subset with closely matched edit geometry, when large enough to describe. Baselines: the local two-candidate rule has zero arm contrast; the exact box-rule indicator has unit contrast. These validate the design. Neither estimates the NCM effect.

**Interpretation.** Positive primary contrast, positive enabling response, similar direction after renaming and a smaller response at unaffected cells support sensitivity to evidence for the named deduction. If C drops while A is unchanged, describe a control-edit effect. A broad gain across the grid is consistent with a more informative puzzle generally. A near-zero estimate with wide uncertainty leaves the question open. Agreement with a human rule can also emerge from pattern recognition or another constraint-propagation procedure. This design tests one behavioral prediction on a selected population. Identifying an internal mechanism requires an intervention.

### 6. Build order and behavioral acceptance

Implement a small local Python package with a command-line entry point. Reuse a host repository’s existing conventions if present. The commands below specify the intended interface for the coding agent to build. They are not commands supplied by the upstream repository.

| Work item | Deliverable | Acceptance |
|---|---|---|
| 1 • Puzzle logic and fixture | Loader, solver, candidate masks, single-rule labels, committed fixture | All §2 assertions pass; reject contradictory clues, a nonunique board and a completed board with a corrupted digit. Repeat after a digit permutation. |
| 2 • Model trace | Frozen CPU adapter; one reference and all three fixture traces | Repeated traces reproduce reference tokens; all K levels present; raw digit scores and full-vocabulary winners agree with the decoder; first plot includes the three actual curves. |
| 3 • Triplet builder | Seeded source split, candidate search, match ranking, reason log | Every accepted family passes the same structural checks; rerun produces the same manifest; splits disjoint; sampling never calls the model. Can proceed independently of item 2. |
| 4 • Pilot | Ten-family target, originals and renamings, timings, first analysis | Independent verification can rebuild sample boards from source rows and edits. Report actual yield and throughput; cache hits produce identical output. |
| 5 • Frozen confirmation | Versioned config, selected family manifest, inference, paired report | Reconstruct the primary estimate from the released family table. Changing an outcome in a synthetic analysis fixture yields the expected signed change. All exclusions and missing rows reconcile. |

Proposed interface (PowerShell-compatible single-line calls):

```powershell
python -m ncm_probe verify-fixture
python -m ncm_probe trace --config configs/pilot.toml --fixture worked-triplet
python -m ncm_probe prepare --config configs/pilot.toml
python -m ncm_probe run --config configs/pilot.toml --resume
python -m ncm_probe report --config configs/pilot.toml
python -m ncm_probe prepare --config configs/confirm.toml
python -m ncm_probe run --config configs/confirm.toml --resume
python -m ncm_probe report --config configs/confirm.toml
```

Record split membership before examining traces. Preparation writes an immutable manifest; run checks its hash. Cache by puzzle, source/model revision, adapter version, precision and decode settings. Write a completed trace atomically after checking shapes and finite scores. A partial file is rerun. Store run metadata and write the analysis from saved traces so changing a plot does not rerun inference.

**Output contract.**

| Artifact | Required contents |
|---|---|
| Run manifest and protocol | Revisions/hashes, environment, settings, seed, split IDs, selection rule, early window, primary metric, search cap, planned n, timestamp before confirmation |
| Family manifest | Family/source IDs, split, A/B/C strings, solution for evaluation, target, d, e, u, edit endpoints, candidate masks, uniqueness certificates or solver results, matching scores, permutation |
| Per-board trace | Board ID, mapping and level lengths, digit logits [K,81,9], full-vocabulary winners [K,81], validity, timing, decoder settings; generated code IDs if available |
| Family-level analysis table | Three early margins, both component responses, primary contrast, levels of stable correctness, final validity, transform ID, control-cell summaries, missing-data flags |
| Figures and short report | Fixture margin trajectories with A/B/C and the early window; cohort paired effects with intervals; secondary stability and rename results; yield, exclusions, costs, limits and interpretation |

**Numerical acceptance example.** Feed a synthetic held-out family with constant early margins A=2.0, B=0.5, C=0.75. The enabling response must be 1.5, control response 0.25, and primary contrast 1.25. An identity copy of B has zero change. If all three curves coincide the primary estimate is zero. Swapping A and C flips the contrast. Failed final boards remain in the calculation. These tests catch errors that leave every software command looking successful.

### 7. Milestones and next decision

**Next work block:** Run the structural fixture test, reproduce an upstream prediction and obtain the first three traces. If the decoder hook consumes the block, finish parity and score extraction before increasing sample size. Next, estimate triplet yield and CPU cost and decide what confirmation precision fits the budget. With five hours per week, the logical first milestone is a validated fixture plot and a small pilot. Confirmation timing depends on the measured yield and run time.

**Conditional mechanism follow-up.** If a target-specific effect replicates, choose a level from development families. Keep B’s puzzle prefix fixed, replace its generated coarse prefix with A’s, recompute the cumulative representation, and generate the remaining levels. Compare B→B self-replay, a C donor of identical depth, and unmodified B under identical settings. Measure the target margin *after subsequent generated levels*, spatial specificity, and solve validity on fresh families. Self-replay must reproduce unmodified B before interpreting any transplant. A whole-prefix transfer tests whether the coarse state carries information that affects later predictions; it also transfers unrelated clues and can produce unnatural states. A successful transfer motivates finer localization. A weak behavioral result calls first for checking readout quality, ceiling effects, match balance and precision. Adaptive stopping is an independent downstream application.

**Handoff instruction.** Build items 1–4, run the real pilot, and return the fixture figure, cohort yield, primary and control estimates, observed CPU cost, and the protocol proposed for confirmation. Execute a frozen confirmation when feasible under the fixed budget and report its status separately from the pilot. State exactly which logical checks and model runs succeeded. Scientific acceptance depends on faithful measurement, including when the hypothesis fails.
