# e0-20261004T103838Z-c58a86-013-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-013-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 939 | 7,692,288 | 86,187 | 1.0029 | 1.4796 | `2f41d03cd974` |
| 1878 | 15,384,576 | 86,006 | 1.0008 | 1.3651 | `2bf972a61826` |
| 3756 | 30,769,152 | 85,858 | 0.9991 | 1.2789 | `7637c2bd1eff` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08627150137128425).
- Individual parity ±1% of target: True.
- Estimated compute: 9.097e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5544 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Eligible at `d_ff` 289, lr 0.003, delta 0.7, seed 0. Val bpb 1.4796/1.3651/1.2789, above
the neutral SwiGLU seed 0 repair at T, 2T and 4T. Not a tuning decision.
