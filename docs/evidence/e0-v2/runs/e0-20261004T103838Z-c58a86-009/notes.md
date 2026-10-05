# e0-20261004T103838Z-c58a86-009

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-009/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 913 | 7,479,296 | 84,845 | 0.9873 | 1.4904 | `30e14e2a4bb8` |
| 1826 | 14,958,592 | 85,038 | 0.9895 | 1.3728 | `97ff08869f77` |
| 3652 | 29,917,184 | 84,944 | 0.9884 | 1.2931 | `6115f5dd433b` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07964830916039234).
- Individual parity ±1% of target: False.
- Estimated compute: 8.642e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3398 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Outside ±1% at nominal `d_ff` 415. The eligible number is the S3 repair at `d_ff` 423.
This original is not an activation result. Neutral MLP selected SwiGLU.
