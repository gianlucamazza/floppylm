# e0-20261004T103838Z-c58a86-103

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-103/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 900 | 7,372,800 | 85,037 | 0.9895 | 1.4750 | `9fb4b5ee7d18` |
| 1800 | 14,745,600 | 84,896 | 0.9879 | 1.3562 | `0d7fb70d9f5d` |
| 3600 | 29,491,200 | 84,659 | 0.9851 | 1.2705 | `cf32e139ddd9` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08571181922886217).
- Individual parity ±1% of target: False.
- Estimated compute: 8.889e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5501 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-07)

Outside ±1% at nominal `d_ff` 171, `d` 96, 4 layers, lr 0.01, delta 0.5, seed 0.
The eligible number is the S3 repair at `d_ff` 176. This original is not a grid result.
