# ncm_explorations
Exploring the reasoning behind Next Concept Modelling, with ablations such as Adaptive Stopping. The end goal is identifying if NCMs can display human-like reasoning (broad concept -> narrow concept -> output communicating concept)

This first study tests whether a frozen medium Sudoku NCM responds to a clue edit that enables a box hidden single. It implements paired A/B/C boards, decoder scores at all 12 levels, independent parity checks, digit-renamed repeats, and family-level analysis. It does not train a model or implement adaptive stopping.

The worked fixture, ten-family pilot and frozen 100-family confirmation have been run. See [RESULTS.md](RESULTS.md) for measured effects, checks and CPU cost. The confirmation does not support the predicted positive early response.

A separate [exploratory code and competitor check](outputs/exploratory-code-competitor-v1/report.md) compares saved code prefixes and readouts at the eliminated competitor. It reuses the already-analyzed cohorts and leaves the primary analysis unchanged. Reproduce it without inference using `python -m scripts.explore_codes_competitor` from this repository.

The follow-up [paired prefix comparison](outputs/exploratory-paired-prefix-v1/report.md) reports A/B and C/B first-divergence counts, the paired four-way counts at every level, and a decomposition of the unchanged primary estimate. Reproduce it with `python -m scripts.explore_paired_prefix`. This analysis is also exploratory and uses saved traces only.

## Start on Windows

Run from this repository in PowerShell with Python 3.11+ and Git installed (the recorded run used Python 3.13.5):

```powershell
.\scripts\setup.ps1
.venv\Scripts\python.exe -m ncm_probe verify-fixture
.venv\Scripts\python.exe -m ncm_probe fetch --config configs/pilot.toml
.venv\Scripts\python.exe -m ncm_probe trace --config configs/pilot.toml --fixture worked-triplet
```

`fetch` caches about 163 MB of public model and data files plus a small upstream code checkout. Immutable revisions, filenames, SHA-256 hashes and licenses are in [asset-lock.json](asset-lock.json). Downloads are local; no paid services are used. Existing assets are checked before use.

For a new installation outside Windows, create a virtual environment, install `requirements-lock.txt`, then `pip install --no-deps -e .`. CPU-first commands work on other platforms; exact score equality across different PyTorch/CPU versions is not assumed. The independent token parity gate must still pass. All commands below also work as `python -m ncm_probe` with the environment activated.

## Pilot and confirmation

```powershell
.venv\Scripts\python.exe -m ncm_probe prepare --config configs/pilot.toml
.venv\Scripts\python.exe -m ncm_probe audit --config configs/pilot.toml
.venv\Scripts\python.exe -m ncm_probe run --config configs/pilot.toml --resume
.venv\Scripts\python.exe -m ncm_probe report --config configs/pilot.toml
.venv\Scripts\python.exe -m ncm_probe prepare --config configs/confirm.toml
.venv\Scripts\python.exe -m ncm_probe audit --config configs/confirm.toml --other-config configs/pilot.toml
.venv\Scripts\python.exe -m ncm_probe run --config configs/confirm.toml --resume
.venv\Scripts\python.exe -m ncm_probe report --config configs/confirm.toml
```

Preparation writes a frozen protocol, all source-family split memberships, and a hashed family manifest. Repeating preparation must reproduce the same manifest. To change a seed, endpoint, selection code or sample size, create a versioned config with a new output directory. A run checks the frozen manifest, and its plan also freezes the adapter/environment identity. Preserve existing study outputs when making later engineering changes. `--resume` reuses validated complete traces and reruns partial or corrupt ones. The compute budget applies per invocation, permitting engineering resumes without changing the sample.

The report command only reads saved traces and writes CSVs, figures, a machine-readable analysis, and a short report. It does not load model weights. Completed traces contain real decoder logits, all-vocabulary winners and generated code IDs; they are kept locally under ignored cache directories. Final puzzle failures stay in the estimate. An inference error is recorded separately as missing data.

The original worked fixture is archived in [ncm_probe/fixtures/worked-triplet.json](ncm_probe/fixtures/worked-triplet.json). See [the supplied experiment packet](docs/experiment-packet.md), [selection protocol](docs/protocol.md), and [measurement/parity details](docs/measurement.md).

## Outputs

- [Fixture figure](outputs/fixture/fixture-margins.png) and [raw target curves](outputs/fixture/fixture-curves.csv). Overlapping lines indicate equal actual readouts.
- [Pilot report](outputs/pilot-v1/report.md), [family analysis](outputs/pilot-v1/family-analysis.csv), and [paired-effect figure](outputs/pilot-v1/cohort-effects.png).
- [Confirmation decision](outputs/confirmation-v1/confirmation-decision.json), [confirmation report](outputs/confirmation-v1/report.md), and [family analysis](outputs/confirmation-v1/family-analysis.csv).
- Each cohort also has `families.json`, `protocol.json`, `independent-audit.json`, `parity.json`, `run-plan.json`, `trace-index.json`, `balance.csv`, and per-level margin and grid-metric tables.

Reconstruct the primary point estimate by filtering `family-analysis.csv` to `transform=original`, `missing=False`, then averaging `specificity`. It is `M_A - M_C`; the early window is levels 1–6. `enabling` and `control` retain A−B and C−B. Renamed rows are paired robustness runs, not additional independent families. Bootstrap intervals use 10,000 seeded resamples of whole families.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp
```

Tests cover the verified fixture, corrupt/conflicting/nonunique boards, exact solver behavior, digit and spatial symmetry grouping, seeded model-blind construction, the numerical analysis acceptance example, full-vocabulary special-token misses, stable correctness, mapping, bootstrap reproducibility, immutable files and cache validation. The real-model parity checks run before inference; CI runs structural and numerical tests without downloading model weights.

The study measures behavioral sensitivity on a selected puzzle population. A matching human deduction is not evidence by itself for a particular internal reasoning mechanism. Mechanism transfers remain a conditional follow-up.

## Separate follow-up: opposite forced answers

This follow-up changes the question: can early preference move toward **opposite correct assignments** when a box hidden single forces d into P versus Q? The original study and its primary result remain separate. See the [predeclared follow-up protocol](docs/opposite-protocol.md).

The ten-family pilot and 100-family confirmation are complete. See [OPPOSITE_RESULTS.md](OPPOSITE_RESULTS.md): early preference tracks the changed assignment under both digit labelings, while the additional rule-over-control advantage is not clearly reproduced after renaming.

Each family has a common 34-clue scaffold with exactly two verified completions. Two rule arms and two remote control arms add one clue of the same digit, yielding four 35-clue, uniquely solvable puzzles. The controls select the same opposing solutions while preserving all target-box candidate locations for d/e and both target cells' local candidates. Geometry matching, residual mismatches, source freshness and split reservations are recorded. The primary is the directional rule shift; the control shift is reported separately and their difference is secondary.

```powershell
.venv\Scripts\python.exe -m ncm_probe.opposite verify-fixture
.venv\Scripts\python.exe -m ncm_probe.opposite prepare --config configs/opposite.toml
.venv\Scripts\python.exe -m ncm_probe.opposite audit --config configs/opposite.toml
.venv\Scripts\python.exe -m ncm_probe.opposite trace --config configs/opposite.toml
.venv\Scripts\python.exe -m ncm_probe.opposite run --config configs/opposite.toml --split pilot --resume
.venv\Scripts\python.exe -m ncm_probe.opposite report --config configs/opposite.toml --split pilot
.venv\Scripts\python.exe -m ncm_probe.opposite run --config configs/opposite.toml --split confirmation --resume
.venv\Scripts\python.exe -m ncm_probe.opposite report --config configs/opposite.toml --split confirmation
.venv\Scripts\python.exe scripts/reproduce_opposite_estimate.py outputs/opposite-v1/confirmation/family-analysis.csv
```

The follow-up freezes ten pilot families and 100 different confirmation families together before any study inference, reserving both solution identities per family. It excludes the prior experiment's scanned families, parity examples and construction-engineering examples. Every split has four original arms plus four digit-renamed repeats per family. The model adapter, weights and deterministic decode settings are unchanged; generator probabilities are not collected. Its [fixture figure](outputs/opposite-v1/fixture/opposite-effects.png), [pilot report](outputs/opposite-v1/pilot/report.md), [confirmation report](outputs/opposite-v1/confirmation/report.md), and [structural audit](outputs/opposite-v1/structural-audit.json) are stored separately.

The [four-board illustration](outputs/opposite-v1/fixture/opposite-boards.png) shows the actual clue edits and marked target locations. P/Q annotations describe blank cells and are never passed to the model. Rebuild it with `python -m scripts.draw_opposite_fixture`. Selected-code secondary tables can be rebuilt with `python -m scripts.opposite_code_summary --split confirmation`.
