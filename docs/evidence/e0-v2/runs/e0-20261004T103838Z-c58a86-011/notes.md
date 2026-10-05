# e0-20261004T103838Z-c58a86-011

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-011/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 907 | 7,430,144 | 83,368 | 0.9701 | 1.5830 | `017ba4c99ce0` |
| 1814 | 14,860,288 | 83,564 | 0.9724 | 1.4460 | `f1c9d734310e` |
| 3628 | 29,720,576 | 83,485 | 0.9715 | 1.3383 | `a80467f2efb0` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.10772433267744908).
- Individual parity ±1% of target: False.
- Estimated compute: 8.540e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5246 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Outside ±1% at nominal `d_ff` 274, lr 0.001, delta 0.7, seed 0. The eligible number is
the S3 repair at `d_ff` 288. This original is not a tuning result.
