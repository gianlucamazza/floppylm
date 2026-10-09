# e0-20261007T164712Z-766d4b-023

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-023/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 770 | 6,307,840 | 85,701 | 0.9972 | 1.5073 | `5199c4c7e8f3` |
| 1540 | 12,615,680 | 85,737 | 0.9977 | 1.3821 | `c63c2200b39f` |
| 3080 | 25,231,360 | 85,762 | 0.9980 | 1.2920 | `9aa18c51ad07` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.09001666446564638).
- Individual parity ±1% of target: True.
- Host init pack: 83,397 B, fill 0.9704, ratio 0.972038; submitted d_ff 303.
- Estimated compute: 6.133e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3439 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-09)

Eligible on the first pack under ADR 0019 and ADR 0020. One 2-bit grid cell,
`d` 80, 3 layers, submitted `d_ff` 303. Not the 2-bit phase selection.
