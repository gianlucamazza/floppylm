# Code map

One line per module; the code is the authority on behaviour, `--help` on flags.

## Library — `src/floppylm/`

```
codec.py         ScalarCodec: ternary / 2bit / 4bit, scales row16 | row8log | tensor16
rans.py          15-bit rANS and bitpack, shortest per tensor, explicit errors
model.py         validated GPTConfig, TinyGPT, nominal bits and FLOPs per token
pack.py          FLP2 ↔ model; pack(unpack(b)) == b; FLP1 rejected (ADR 0006)
shapes.py        shape solver: d, n_layers, free d_ff at 99.5–100% of the budget
train.py         WSD with trunk and cooldowns, checkpoints, sliding evaluation
parity.py        eligibility on serialized bytes, paired σ
metrics.py       bits per byte (byte tokenizer: one token is one byte)
seed.py          single RNG entry point (ADR 0003 §3)
runlog.py        unique ids, exclusive directories, atomic writes, state, manifests
data.py          TinyStoriesV2: exact dedup, hash split, manifest, reproducibility
bpe.py           train-only byte-exact BPE oracle (E1 functional qualification, ADR 0013)
vq.py            standalone vector-weight oracles (E1 functional qualification, ADR 0013)
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
| `e0_campaign.py`               | Sequential frozen Xbox E0 campaign                     | `--out` `--acceptance` `--benchmark` `--recover`                                                                                                                                                                 |
| `xbox_acceptance.py`           | Operation cases, model fixtures, optimizer, resume     | `--out`                                                                                                                                                                                                          |
| `xbox_benchmark.py`            | Representative synthetic throughput                    | `--out` `--acceptance` `--steps` `--summarize`                                                                                                                                                                                 |
| `xbox_worker_acceptance.py`    | Identity/oversized rejection and worker reuse          | `--out` `--expect-broken`                                                                                                                                                                                        |
| `xbox_recovery_acceptance.py`  | Interrupted and completed recovery                     | `--out` `--acceptance`                                                                                                                                                                                           |
| `xbox_lifecycle_acceptance.py` | Real suspension and checkpoint lifecycle               | `--out` `--acceptance`                                                                                                                                                                                           |

## Contracts — `schemas/`

JSON Schemas of every file exchanged with the native backend; see [schemas/README.md](../../schemas/README.md).

## Scripts and tests

- `scripts/e0_status.py --campaign DIR [--xbox]`: read-only local/live campaign state and
  frozen-source checks; with `--xbox` also reports whether `XgpuE0.exe` is in the
  process list. Exit code 1 on issues.
- `scripts/e0_recover.py --out DIR --acceptance FILE --benchmark FILE`: explicit operator
  recover. Starts the bound package with `openappx deploy --start` only when the
  process is missing, waits for a live worker, then execs `e0_campaign.py --recover`.
- `scripts/e1_qualify.py`, `scripts/e1_cpu_profile.py`: ADR 0013 functional qualification and the
  scalar CPU profile ([evidence](../evidence/e1-qualification-20261001/notes.md)).
- `scripts/contract_fixtures.py`: regenerate the golden contract instances in
  `tests/fixtures/contracts/`.
- `tests/`: regressions for every module, including the FLP1 fixture for the rejection test.
  Run with `pytest`.
