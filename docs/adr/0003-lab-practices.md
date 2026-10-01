# ADR 0003: Lab practices

## Status

`superseded-in-part` — accepted 2026-09-30, amended 2026-09-30, amended 2026-10-01.
Superseded in part by [ADR 0005](0005-e0v2-protocol.md): §2 and §7.

## Context

SmallerGPT, a sibling lab project, closed two lines because the exotic idea did not beat a
trivial adversary; the lab practices inherited from that project made those closures credible.
Here the specific risk is different: **cheating on the byte count** ("free" tokenizer,
excluded runtime, seeds that hide data).

## Decision

1. Every condition prints `image_bytes` (total), `runtime_bytes`, `tokenizer_bytes`,
   `model_bytes`, `effective_params`. The number that counts is `image_bytes`, counted on the
   real file, not estimated.
2. A comparison between conditions whose `image_bytes` differ by more than 1% is invalid.
3. `seed_all(n)` is the only RNG entry point. The seeds of procedural generators are part
   of the description and are counted in the bytes.
4. Evidence = `summary.json` + `notes.md` in `docs/evidence/e<N>-<tag>/`. Without notes the run
   is not measured.
5. Stop on F\*: if F1 triggers in E1, E2–E4 become _won't run_ for the procedural thesis.
6. Harness without flags → help, exit 2. Explicit `--smoke` / `--full`. Long jobs: see amendment.
7. Held-out split fixed in E0 and never touched by training or by hyperparameter selection.
8. Ruff format+lint on Python; `clang-format` on the C runtime.

## Consequences

- Bit accounting is tested code, not a table in the docs.
- No hyperparameter is chosen by looking at the held-out set.

## Amendment — 2026-09-30

Point 6 changes by user decision: training jobs do **not** run in `background.slice`.
The slice has a fixed quota of 1 core (`cpu.max 100000 100000`): with 4 threads training used
~0.7 core and every estimate in [R6](../research/06-hardware-budget.md) had to be multiplied by ~4.
Jobs start with `nohup` and log to `runs/*.log`, with 4 threads; the thermal governor remains the
only limit.

## Amendment — 2026-10-01 (documentation refactor)

The decisions above are unchanged except where they no longer match the repository:

- **§4 evidence path.** The `docs/evidence/e<N>-<tag>/` pattern is superseded by the actual
  layout documented in [docs/evidence/README.md](../evidence/README.md):
  `e0-v2/runs/<run-id>/`, `e0-v2/campaigns/<campaign-id>/`, `e0-v2/selections/` and
  `xbox-e0-YYYYMMDD[-tag]/`.
- **§6 `--smoke` / `--full`.** `experiments/e0_v2.py` has `--smoke` only; a run without
  `--smoke` is the full run.
- **§8 `clang-format`.** Applies only once a C runtime exists; none exists yet.
