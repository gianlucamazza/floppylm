# e0-20261007T164712Z-766d4b-024

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-024/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 764 | 6,258,688 | 85,621 | 0.9963 | 1.5258 | `98e44599db11` |
| 1528 | 12,517,376 | 85,798 | 0.9984 | 1.3912 | `6897bd36ff16` |
| 3056 | 25,034,752 | 85,608 | 0.9962 | 1.2944 | `21c6a742f736` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.09673394136389168).
- Individual parity ±1% of target: True.
- Host init pack: 83,494 B, fill 0.9716, ratio 0.973192; submitted d_ff 198.
- Estimated compute: 6.374e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4687 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-09)

Eligible on the first pack under ADR 0019 and ADR 0020. One 2-bit grid cell,
`d` 80, 4 layers, submitted `d_ff` 198. Not the 2-bit phase selection.
