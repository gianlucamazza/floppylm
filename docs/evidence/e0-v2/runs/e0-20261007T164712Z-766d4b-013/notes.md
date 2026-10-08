# e0-20261007T164712Z-766d4b-013

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-013/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 762 | 6,242,304 | 85,274 | 0.9923 | 1.6345 | `75a849d95037` |
| 1524 | 12,484,608 | 85,408 | 0.9938 | 1.4702 | `9fcc3b4467ec` |
| 3048 | 24,969,216 | 85,643 | 0.9966 | 1.3559 | `c10b1e004123` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.11432926224799744).
- Individual parity ±1% of target: True.
- Host init pack: 83,274 B, fill 0.9690, ratio 0.970017; submitted d_ff 205.
- Estimated compute: 6.216e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3427 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-08)

Eligible on the first pack under ADR 0019 and ADR 0020. 2-bit tuning on the
neutral shape, lr 0.001, wd 0, submitted `d_ff` 205. One tuning cell of campaign
`e0-20261007T164712Z-766d4b`. Not a format decision.
