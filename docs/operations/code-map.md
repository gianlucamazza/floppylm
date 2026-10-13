# Code map

One line per module; the code is the authority on behaviour, `--help` on flags.
How the layers fit is [architecture](../architecture.md).

## Library — `src/floppylm/`

```
codec.py         ScalarCodec: ternary / 2bit / 4bit, scales row16 | row8log | tensor16
rans.py          15-bit rANS and bitpack, shortest per tensor, explicit errors
model.py         validated GPTConfig, TinyGPT; a vq core takes a VectorBook, not a config field
pack.py          FLP2 ↔ model; one VQB1 when core_fmt is vq; held assignment packed as-is; FLP1 rejected
shapes.py        shape solver: d, n_layers, free d_ff at 99.5–100% of the budget
train.py         WSD trunk and cooldowns; trunk checkpoint every 64 steps and before each cooldown, storing trunk steps and seconds; a vq core assigns every 64 steps at probability 0.1
parity.py        eligibility on serialized bytes, paired σ
metrics.py       bits per byte (byte tokenizer: one token is one byte)
seed.py          single RNG entry point (ADR 0003 §3)
runlog.py        unique ids, exclusive directories, atomic writes, state, manifests
data.py          TinyStoriesV2: exact dedup, hash split, manifest, reproducibility
bpe.py           train-only byte-exact BPE oracle (E1 functional qualification, ADR 0013)
vq.py            VQB1 book and vector oracle; learned reseeds continue the PCG32 stream; VQF1 stays a fixture
e1_plan.py       1/16 host plan: stored scalar arms, four G=8 books, ADR 0024 seed-0 solver, F1. Does not train. All four G=8 seed-0 books are closed. T is 20780800. Live cell state is in STATUS.md
e1_pilot.py      1/16 CPU campaign path: shared T, seeds 0/1/2, cooldowns at T/2T/4T, one S3, one freeze, one final test. The synthetic smoke is not a result. The signal publisher reads eighteen closed cells and does not publish until they exist. The reserved final test is the one test-split read. Cell ternary-s0 is closed. S3 repaired d_ff 262 to 266. The repair is eligible and is not the signal. Trunk seconds were not saved. Cell ternary-s1 is closed and ineligible. Cell ternary-s2 is closed and eligible. S3 repaired d_ff 262 to 267. It is not the signal. Cell 2bit-s0 is closed and eligible. d_ff stayed 205. Cell 2bit-s1 is closed and eligible. d_ff stayed 205. Cell 2bit-s2 is closed and eligible. d_ff stayed 205. It is not the signal. A dead lock resumes trunk.pt and does not redo a cooldown whose branch file is already at that boundary. Cell vq-0.5-fixed-s0 is training and is not closed. It is not the signal. The other eleven cells have not started. No signal is published
```

## Xbox execution — `src/floppylm_xbox/`

Depends on the core package; the core never imports it ([ADR 0012](../adr/0012-repo-boundaries.md)).

```
jobs.py          portable E0 jobs and independent numerical gates for the native backend
kernels.py       independent PyTorch/autograd oracle for each native tensor operation
portal.py        Device Portal: settings, pinned TLS, verified assets, submission, recovery
```

## Experiments — `experiments/`

| Script                         | Purpose                                                | Main flags                                                                                                                                                                                                       |
| ------------------------------ | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `e0_v2.py`                     | E0 v2 harness: plan, train, grid, parity, freeze, test | modes `--plan` `--run` `--resume` `--retry` `--grid` `--parity` `--freeze` `--final-test` `--verify-data`; `--smoke`, `--functional`, `--name` (required by `--freeze`), `--backend cpu\|xbox`, `--xbox-acceptance`, `--run-id`, `--threads`, `--jobs`, `--val-bytes`, `--budget-frac`, `--tokens`, `--branches`, shape/recipe flags |
| `e0_campaign.py`               | Sequential frozen Xbox E0 campaign                     | `--out` `--acceptance` `--benchmark` `--recover` `--lifecycle-tool` `--lifecycle-config` `--allow-orphan` `--on-tool-unreachable` `--heartbeat-interval-seconds`                                                                     |
| `xbox_acceptance.py`           | Operation cases, model fixtures, optimizer, resume     | `--out`                                                                                                                                                                                                          |
| `xbox_benchmark.py`            | Representative synthetic throughput                    | `--out` `--acceptance` `--steps` `--summarize`                                                                                                                                                                                 |
| `xbox_worker_acceptance.py`    | Identity/oversized rejection and worker reuse          | `--out` `--expect-broken`                                                                                                                                                                                        |
| `xbox_recovery_acceptance.py`  | Interrupted and completed recovery                     | `--out` `--acceptance`                                                                                                                                                                                           |
| `xbox_lifecycle_acceptance.py` | Real suspension and checkpoint lifecycle               | `--out` `--acceptance`                                                                                                                                                                                           |

`experiments/xbox_watchdog_acceptance.py`: real-deadline functional watchdog,
process exit and exact-recovery acceptance; no scientific campaign.

## Contracts — `schemas/`

JSON Schemas of every file exchanged with the native backend; see [schemas/README.md](../../schemas/README.md).

## Scripts and tests

- `scripts/e0_status.py --campaign DIR [--xbox]`: read-only local/live campaign state and
  frozen-source checks; with `--xbox` also reports whether `XgpuE0.exe` is in the
  process list. Exit code 1 on issues.
- `scripts/e0_recover.py --out DIR --acceptance FILE --benchmark FILE`: explicit operator
  recover. Starts the bound package with `openappx deploy --start` only when the
  process is missing, waits for a live worker, then execs `e0_campaign.py --recover`.
- `scripts/e0_console_teardown.py --campaign DIR`: unit `ExecStop` helper. Invokes
  xbox-gpu-training `e0_console_lifecycle.py` `teardown` then `idle-gpu --when after`
  ([PR #46](https://github.com/gianlucamazza/xbox-gpu-training/pull/46)). Settings:
  [lifecycle config](e0-console-lifecycle.md). Records into `campaign.json` /
  `summary.json`; an unreachable tool or console is logged and does not raise.
- `units/floppylm-e0-campaign@.service`: user-unit template; `EnvironmentFile=` for
  xbox.env and e0-lifecycle.env; `ExecStop` teardown.
- `scripts/e1_qualify.py`, `scripts/e1_cpu_profile.py`: ADR 0013 functional qualification and the
  scalar CPU profile ([evidence](../evidence/e1-qualification-20261001/notes.md)).
- `scripts/contract_fixtures.py`: regenerate the golden contract instances in
  `tests/fixtures/contracts/`.
- `tests/`: regressions for every module, including the FLP1 fixture for the rejection test.
  Run with `pytest`.

Read-only preparation: `scripts/e0_preflight.py --acceptance PATH --benchmark PATH --data-manifest PATH [--data-dir PATH] [--xbox]`; JSON stdout, no campaign or final-test writes. Protocol values are shared with the launcher through `floppylm.campaign_protocol`. See [launch packet](e0-launch-packet.md).
