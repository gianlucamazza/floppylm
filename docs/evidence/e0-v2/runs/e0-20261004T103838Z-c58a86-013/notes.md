# e0-20261004T103838Z-c58a86-013

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-013/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 907 | 7,430,144 | 83,614 | 0.9730 | 1.4731 | `fbb2282a0940` |
| 1814 | 14,860,288 | 83,372 | 0.9701 | 1.3650 | `74aa5f54b77a` |
| 3628 | 29,720,576 | 83,248 | 0.9687 | 1.2873 | `be915d0b3fd0` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07766689369634383).
- Individual parity ±1% of target: False.
- Estimated compute: 8.540e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5245 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Outside ±1% at nominal `d_ff` 274, lr 0.003, delta 0.7, seed 0. The eligible number is
the S3 repair at `d_ff` 289. This original is not a tuning result.
