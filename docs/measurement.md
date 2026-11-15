# Measurement and parity

The experiment follows the supplied packet's initial-clue box hidden-single design. The model adapter's `trace(board)` accepts only the 81 clue cells. Solutions, correct digits, targets and rule labels remain in preprocessing and evaluation. It loads the medium generator and tokenizer in evaluation mode, disables gradients, uses CPU float32, four intra-op threads, one board per batch, deterministic algorithms, and the release's greedy settings. No weights change.

## Mapping

Sudoku output tokens are 89 positions: nine digits per row with separator 10 between rows. Board cell `(r,c)` maps to offset `10*r+c` for zero-based coordinates. Digits 1–9 map to vocabulary IDs 1–9; blank is 0 and BOS is 11. The 91-token input is BOS, the 89 puzzle tokens, BOS. There is no padding. Mapping validation exercises every digit at every cell through the pinned upstream tokenizer, including row and board boundaries.

## Intermediate reconstruction

The release has 12 levels of lengths 1, 2, 4, 6, 9, 13, 18, 26, 37, 50, 67, 89. Upstream `generate` constructs prefixes, attention masks and greedy code choices unchanged. Only after generation, the adapter replays `get_next_autoregressive_input` on the generated code IDs. At each level it immediately decodes a clone of the full 89-position cumulative latent. This includes upstream interpolation and residual reconstruction operators.

This avoids a source pitfall: at the pinned revision, `idx_to_zhats(...)[0]` appends references to an accumulator subsequently modified in place. Its other returned list contains downsampled generation inputs, whose variable lengths do not provide an 81-cell measurement. Decoding clones of the full cumulative representation produces the full-length readout used in the independent reference export.

Every trace stores the actual decoder scores before argmax: digit logits `[12,81,9]` and an additional full-vocabulary audit tensor `[12,89,12]`. It retains raw output tokens `[12,89]`, cell winners `[12,81]`, all 322 code IDs, timing and peak process memory. Special-token winners remain misses. Original clues are never written over predictions; upstream generation does not enforce them internally.

## Parity gates

Before running a cohort, both published medium reference inputs are checked against the pinned independent PyTorch fixtures:

1. All generated code IDs match.
2. All 12 levels' full-length output tokens match.
3. Running the instrumented readout twice produces exactly equal raw scores.
4. A separate run without intermediate readout agrees in code IDs and final tokens with upstream `vqvae.decode`.
5. Shapes, finiteness, digit mapping and full-vocabulary argmax agree at every saved position.

A mismatch raises an error before cohort inference. There are no pseudo-logits or silent hard-label fallbacks. Readout and generation happen in separate phases, so reading intermediate states does not alter code selection.

## Primary analysis

Use one-based levels 1–6, equally weighted. At the target, subtract the rival digit's decoder score from the correct digit's score; average these margins within each arm. Report enabling A−B, control C−B, and primary specificity A−C. All complete triplets enter, including incorrect final grids. Original families are primary; digit-renamed repeats are reported separately. Bootstrap draws resample whole families 10,000 times with the frozen seed. The stability endpoint uses the full-vocabulary winner, with 13 meaning never permanently correct by level 12.

Reports read saved traces; plotting does not require model inference. Trace identities include model/data revisions and hashes, adapter source hash, environment, precision, mapping, threads and decode settings. Corrupt or incomplete cache files are rerun with `--resume`. Engineering failures have separate missing-data records and never count as Sudoku failures.

Sources: [upstream code](https://github.com/HazyResearch/ncm/tree/c70274273f489abc73832b2b98584a8483b6b203), [checkpoints](https://huggingface.co/hazyresearch/ncm-checkpoints/tree/d342ce8aaea58830eef3b8ad473664673e41f692/sudoku/medium), [source boards](https://huggingface.co/datasets/hazyresearch/ncm-datasets/tree/6580ba41a4b0a976dde876fbe84d25327617b0e6/sudoku/medium), and [independent parity export](https://huggingface.co/mrfakename/ncm-webgpu-weights). Exact parity revision and file hashes are in `asset-lock.json` and each protocol. These public assets list MIT licenses.
