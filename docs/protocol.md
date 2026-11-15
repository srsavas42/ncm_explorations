# Frozen selection and analysis protocol

Each solved-grid family contributes one target and one A/B/C triplet. Preparation never imports or calls the model. The archived worked fixture is outside the source cohorts.

Source solutions are grouped by first-occurrence digit canonicalization and all eight square dihedral transformations. Other unidentified Sudoku automorphisms, such as arbitrary within-band row permutations, are not exhaustively detected. Split assignment hashes seed and family ID: modulo five equal to zero is pilot; other families are confirmation. The split membership of all source families is written before searching or tracing. Sources are visited in a seeded shuffled order.

Only forward search is allowed: source=B. Require 35 clues and exactly one completion equal to the supplied solution. Targets must have two immediate candidates including their correct digit, exactly two eligible correct-digit positions in their box, and at least two in their own row and column. Targets are shuffled with the frozen generator and the first target with an eligible triplet is selected.

Enumerate all moves of the correct digit between a given and a previously blank cell in the supplied solution. Both endpoints are outside the target and its peers. Require unchanged direct peer clues, target candidates, digit frequencies and clue count. A must force only the target in its box; C must retain exactly B's two eligible box positions. Neither target row nor column may force the digit in any arm. Exact solution counting checks every retained variant.

For the selected target, rank all eligible A/C combinations lexicographically:

1. Prefer the same removed clue.
2. Minimize endpoint geometry L1 mismatch. Each endpoint has a vector: same band as target, same stack, absolute row distance, absolute column distance. Compare removal with removal and reveal with reveal.
3. Minimize target row/column eligible-count L1 mismatch.
4. Minimize the absolute difference in initially forced cells. Count the union of naked-single cells and hidden-single cells over all units from initial candidates.
5. Break exact ties with the seeded random generator.

The manifest records raw geometry, ranking components, rule masks, source row IDs, edit endpoints, target, rival, competitor and exact solver result. Search stops at the planned number of complete triplets or the fixed source-row budget; model scores never affect it. Counts describe the source rows and target/move candidates actually examined. A/B-only targets are counted separately and excluded from paired estimates; no A/B-only model analysis is performed in this version.

One seeded nonidentity digit permutation per family applies consistently to all arms, solution and evaluation labels. Exact structural checks repeat after transformation, followed by an inverse-map round trip. Renamed results never increase the primary family sample size.

The initial pilot target is 10. Confirmation retains the predeclared planning target of 100, capped at 100, with a source scan cap of 2,000 rows and a compute cap of 14,400 seconds per invocation. Its proposed useful interval half-width is 0.5 decoder logit units. The early window remains levels 1–6. The saved confirmation decision uses pilot SD and latency to document feasibility before reading confirmation outcomes. The estimate 1.96×SD/√n is a planning approximation; the reported interval is the seeded family percentile bootstrap. Reaching n=100 is not a guarantee of the precision goal. Small matched subsets are descriptive.

Spatial controls are predetermined cells blank in all three arms with the same two local candidates and the same row/column/box hidden-single labels for their own correct digit. Average their effects once per family; report coverage. The descriptive closely matched subset requires the same removed clue, identical target row/column counts and endpoint geometry L1 ≤ 6. It does not replace the primary cohort.

All selected families and splits remain frozen even when the model fails to solve. Engineering failures may be resumed and are explicitly reconciled by arm; only complete triplets contribute to each transform's paired analysis. This is a behavioral test on a selected population. Preference strength, stable correctness, spatial specificity and final Sudoku validity answer distinct questions. No mechanism interventions, model training or adaptive stopping are included.
