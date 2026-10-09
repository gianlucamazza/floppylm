# e0-20261007T164712Z-766d4b-021

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-021/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 753 | 6,168,576 | 85,273 | 0.9923 | 1.5353 | `4a42de4263a7` |
| 1506 | 12,337,152 | 85,354 | 0.9932 | 1.3995 | `4e510c2de100` |
| 3012 | 24,674,304 | 85,146 | 0.9908 | 1.2987 | `91ae434255a5` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.10080242113100146).
- Individual parity ±1% of target: True.
- Host init pack: 83,946 B, fill 0.9768, ratio 0.978528; submitted d_ff 132.
- Estimated compute: 6.733e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5096 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-09)

Eligible on the first pack under ADR 0019 and ADR 0020. One 2-bit grid cell,
`d` 64, 7 layers, submitted `d_ff` 132. Not the 2-bit phase selection.
