# e0-20261004T103838Z-c58a86-007-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-007-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 920 | 7,536,640 | 85,853 | 0.9990 | 1.4694 | `d81a7048306d` |
| 1840 | 15,073,280 | 85,976 | 1.0004 | 1.3544 | `ffb7b7f92f67` |
| 3680 | 30,146,560 | 85,820 | 0.9986 | 1.2793 | `6fd15a4ef9d5` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07507772610321606).
- Individual parity ±1% of target: True.
- Estimated compute: 8.766e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4758 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Eligible S3 repair, `d_ff` 280. Val bpb 1.4694/1.3544/1.2793 is SwiGLU seed 1.
With seed 0 the mean is 1.4631/1.3473/1.2704. Two seeds are not an activation
selection while ReLU² seed 1 is still open.
