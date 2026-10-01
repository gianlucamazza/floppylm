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
xbox.py          portable E0 jobs and independent numerical gates for the native backend
xbox_kernels.py  independent PyTorch/autograd oracle for each native tensor operation
xbox_portal.py   Device Portal: verified assets, submission binding, transport, recovery
```

## Experiments — `experiments/`

| Script                         | Purpose                                                | Main flags                                                                                                                                                                                                       |
| ------------------------------ | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `e0_v2.py`                     | E0 v2 harness: plan, train, grid, parity, freeze, test | modes `--plan` `--run` `--resume` `--retry` `--grid` `--parity` `--freeze` `--final-test` `--verify-data`; `--smoke`, `--functional`, `--backend cpu\|xbox`, `--xbox-acceptance`, `--run-id`, shape/recipe flags |
| `e0_campaign.py`               | Sequential frozen Xbox E0 campaign                     | `--out` `--acceptance` `--benchmark` `--recover`                                                                                                                                                                 |
| `xbox_acceptance.py`           | Operation cases, model fixtures, optimizer, resume     | `--out`                                                                                                                                                                                                          |
| `xbox_benchmark.py`            | Representative synthetic throughput                    | `--out` `--acceptance` `--steps`                                                                                                                                                                                 |
| `xbox_worker_acceptance.py`    | Identity/oversized rejection and worker reuse          | `--out` `--expect-broken`                                                                                                                                                                                        |
| `xbox_recovery_acceptance.py`  | Interrupted and completed recovery                     | `--out` `--acceptance`                                                                                                                                                                                           |
| `xbox_lifecycle_acceptance.py` | Real suspension and checkpoint lifecycle               | `--out` `--acceptance`                                                                                                                                                                                           |

## Scripts and tests

- `scripts/e0_status.py --campaign DIR [--xbox]`: read-only local/live campaign state and
  frozen-source checks; exit code 1 on issues.
- `tests/`: regressions for every module, including the FLP1 fixture for the rejection test.
  Run with `pytest`.
