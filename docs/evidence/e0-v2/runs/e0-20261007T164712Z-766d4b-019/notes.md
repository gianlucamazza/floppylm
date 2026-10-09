# e0-20261007T164712Z-766d4b-019

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-019/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 765 | 6,266,880 | 85,463 | 0.9945 | 1.5163 | `3332a6cbed94` |
| 1530 | 12,533,760 | 85,684 | 0.9971 | 1.3787 | `2c158bb57901` |
| 3060 | 25,067,520 | 85,568 | 0.9957 | 1.2841 | `be0a32d2759b` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.09460974855965776).
- Individual parity ±1% of target: True.
- Host init pack: 83,681 B, fill 0.9737, ratio 0.976122; submitted d_ff 224.
- Estimated compute: 6.390e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4779 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-09)

Eligible on the first pack under ADR 0019 and ADR 0020. One 2-bit grid cell,
`d` 64, 5 layers, submitted `d_ff` 224. Not the 2-bit phase selection.
