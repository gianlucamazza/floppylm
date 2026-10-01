# E0-lite pre-v2 — diagnostics, excluded from verdicts

Two runs of the scalar grid at 1/16, stopped on 2026-09-30 because invalid as a comparison
([ADR 0005](../../../adr/0005-e0v2-protocol.md)): budget fill 0.88 vs 0.92 (parity
violated), non-saturated cosine schedule, untuned adversary, test evaluated inside the run.

| Run                     | Bytes  | val bpb            | test bpb           | blob sha256                                                        |
| ----------------------- | ------ | ------------------ | ------------------ | ------------------------------------------------------------------ |
| `b16-ternary-d64-l6-s0` | 75 942 | 2.0129680935772494 | 2.0154060906348845 | `514991ca5b71a5503f27a9b8991919ef1780089a3519bff43c0ed0beb3e01cf6` |
| `b16-ternary-d80-l4-s0` | 78 627 | 1.8551768137161695 | 1.8632087339879280 | `f32745d175872a0c673ad9eee5f2a9d47232d000c18ce841ccbe5366f93a8baf` |

Smoke of the same code: `runs/smoke/model.flp`, 7 713 B, sha256
`1dfae3659fcd4bfe09e7a43641fe70c251ef5e66dd5ff7e147197fee2f34c79d` (copy in
`tests/fixtures/flp1_smoke.flp`).

## What is known and what is not

- The JSON files in this folder are the original output of the `e0_lite.py` harness, unmodified.
- The blobs live in `runs/<tag>/model.flp`, outside Git. They are in **`FLP1` format, no longer
  readable by the active code** ([ADR 0006](../../../adr/0006-flp2-only.md)); they can be read at
  Git revision `f9e0732`, where the val bpb values above were reproduced exactly.
- Pre-v2 evaluation protocol: non-overlapping 257-byte windows, first MiB of val and
  first 2 MiB of test; 256-byte context, byte tokenizer.
- **Not available**, and not reconstructed: code hash at run time (the Git repo did not
  exist yet), hashes of the data files used, exact environment. `experiments/e0_lite.py` at revision
  `f9e0732` has the same logic used for the runs (only docstrings and help texts change), but there
  it is no longer runnable: it imports `floppylm.quant`, already replaced by `codec.py`.
