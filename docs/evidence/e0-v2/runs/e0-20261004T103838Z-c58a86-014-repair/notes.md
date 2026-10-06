# e0-20261004T103838Z-c58a86-014-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-014-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 922 | 7,553,024 | 86,220 | 1.0033 | 1.4602 | `3cbc89a2ac5e` |
| 1844 | 15,106,048 | 86,141 | 1.0024 | 1.3481 | `0dfa8ec99197` |
| 3688 | 30,212,096 | 85,911 | 0.9997 | 1.2720 | `852b41267ede` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07608664766716733).
- Individual parity ±1% of target: True.
- Estimated compute: 8.800e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5401 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-06)

Eligible at `d_ff` 281, lr 0.01, delta 0.5, seed 0. Val bpb 1.4602/1.3481/1.2720, the
lowest of the six ternary tuning cells at T, 2T and 4T. The grid uses this learning rate
and delta. Above the neutral SwiGLU seed 0 repair. Not a finished shape.
