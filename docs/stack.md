# Stack

Owner of languages, toolchain and machine constraints. It does not own the thesis or live state.

## Languages and tools

- Training and experiments: Python ≥ 3.12, PyTorch ≥ 2.4 (CPU path), `numpy`
  ([`pyproject.toml`](../pyproject.toml)). Dev: `pytest`, `ruff` (line length 100). A local
  `.venv` with `pip install -e '.[dev]'` is the usual host setup ([CONTRIBUTING.md](../CONTRIBUTING.md));
  scripts and pytest also put `src/` on the path.
- Xbox backend: a separate DX12/UWP trainer in the
  [xbox-gpu-training](https://github.com/gianlucamazza/xbox-gpu-training) repository, driven from
  here through Device Portal (`src/floppylm_xbox/`). This repository owns all FloppyLM semantics;
  the backend only executes them ([ADR 0009](adr/0009-xbox-e0-backend.md),
  [ADR 0012](adr/0012-repo-boundaries.md)).
- Runtime (E3/E4, not yet written): C99 derived from llama2.c's `run.c`, static with musl, `-Os`,
  stripped ([R4](research/04-runtime-and-demoscene.md)).
- Generators: xorshift/PCG/Philox implemented identically in C and Python, with bit-exact parity
  tests.
- Docs and code comments: English.

## Machines

- **Host**: Lenovo i7-1165G7, 4C/8T, 32 GB, Iris Xe without CUDA. Measured: 92–117 GFLOPS fp32 in
  bursts, ~23 GB/s, slow bf16 (not native), AVX512-VNNI for int8 ([R6](research/06-hardware-budget.md)).
  It prepares data, runs the Python oracle and evaluation, and drives the Xbox. Long jobs run
  under `systemd-run --user` with linger, through `bg` in `background.slice`, following
  the current owner instruction (observed quota: one CPU). This overrides the historical
  `app.slice` exception for new launches. Logs live in `runs/` ([runbook](operations/xbox-e0.md),
  [ADR 0003](adr/0003-lab-practices.md), [ADR 0017](adr/0017-runtime-liveness.md)).
- **Xbox Series S** (retail, Dev Mode): E0 training at 1/16 on the hardware GPU
  ([ADR 0009](adr/0009-xbox-e0-backend.md)); operations in the [runbook](operations/xbox-e0.md).
- No GPU rental or paid service in the approved scope ([completion plan](completion-plan.md));
  changing that requires a dedicated ADR.

## What is versioned

Docs, ADRs, surveys, code, and evidence (`summary.json`, `notes.md` and the JSON proofs under
`docs/evidence/`). Corpora (`data/`), run directories (`runs/`), checkpoints and `.img`/`.flp`
images stay out of git; the number lives in the tracked JSON.
