# e0-20261004T103838Z-c58a86-012-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-012-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 918 | 7,520,256 | 85,708 | 0.9973 | 1.4829 | `c7fc57a9de93` |
| 1836 | 15,040,512 | 85,706 | 0.9973 | 1.3593 | `3069332cfbfc` |
| 3672 | 30,081,024 | 85,722 | 0.9975 | 1.2772 | `0ac646762725` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08216745011746363).
- Individual parity ±1% of target: True.
- Estimated compute: 8.727e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5345 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Eligible at `d_ff` 279, lr 0.003, delta 0.5, seed 0. Val bpb 1.4829/1.3593/1.2772, above
the neutral SwiGLU seed 0 repair (trial `006-repair`, `d_ff` 280) at T, 2T and 4T. Not a
tuning decision.
