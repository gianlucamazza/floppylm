# e0-20261007T164712Z-766d4b-005

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-005/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 914 | 7,487,488 | 85,288 | 0.9924 | 1.4599 | `f67b5c5d0346` |
| 1828 | 14,974,976 | 85,185 | 0.9912 | 1.3375 | `a4c92e422922` |
| 3656 | 29,949,952 | 85,098 | 0.9902 | 1.2522 | `0c1a4a8ff18e` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08531008553573716).
- Individual parity ±1% of target: True.
- Host init pack: 85,223 B, fill 0.9917, ratio 0.993452; submitted d_ff 262.
- Estimated compute: 8.812e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5523 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-08)

Eligible on the first pack under ADR 0019 and ADR 0020. The three cooldown
artifacts match `e0-20261004T103838Z-c58a86-022-r3`. One grid cell of campaign `e0-20261007T164712Z-766d4b`.
Not a shape decision.

## Later (2026-10-08)

The ternary grid comparison is byte-comparable and rank-stable at T, 2T and 4T.
This cell is the stored ternary phase selection (`d` 80, 4 layers, `d_ff` 262,
lr 0.01, wd 0.1). It is not the scalar recipe. 2-bit tuning, the 2-bit grid,
paired seeds and the final test remain.
