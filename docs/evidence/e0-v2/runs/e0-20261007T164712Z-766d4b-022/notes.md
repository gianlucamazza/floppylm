# e0-20261007T164712Z-766d4b-022

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-022/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 750 | 6,144,000 | 85,511 | 0.9950 | 1.5482 | `a7ecdea6fb33` |
| 1500 | 12,288,000 | 85,438 | 0.9942 | 1.4081 | `c86d7561ef80` |
| 3000 | 24,576,000 | 85,474 | 0.9946 | 1.3080 | `d86bfdd438da` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.10005477781920313).
- Individual parity ±1% of target: True.
- Host init pack: 83,878 B, fill 0.9760, ratio 0.979677; submitted d_ff 104.
- Estimated compute: 6.947e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  6015 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-09)

Eligible on the first pack under ADR 0019 and ADR 0020. One 2-bit grid cell,
`d` 64, 8 layers, submitted `d_ff` 104. Not the 2-bit phase selection.
