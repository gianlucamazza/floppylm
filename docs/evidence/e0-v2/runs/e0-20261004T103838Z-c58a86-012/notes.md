# e0-20261004T103838Z-c58a86-012

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-012/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 907 | 7,430,144 | 84,719 | 0.9858 | 1.4660 | `a658b887f64d` |
| 1814 | 14,860,288 | 84,939 | 0.9884 | 1.3503 | `b1d670e87882` |
| 3628 | 29,720,576 | 84,912 | 0.9881 | 1.2730 | `f474f594cc1d` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07720732599770885).
- Individual parity ±1% of target: False.
- Estimated compute: 8.540e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5240 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Same recipe as trial `006` (lr 0.003, delta 0.5, nominal `d_ff` 274, seed 0). The
artifact differs from `006` and is outside ±1%. The eligible number is the S3 repair at
`d_ff` 279. This original is not a tuning result.
