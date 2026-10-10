# e0-20261009T174028Z-94847b-004

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-004/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 914 | 7,487,488 | 85,084 | 0.9901 | 1.4585 | `60bb0f1e6256` |
| 1828 | 14,974,976 | 85,140 | 0.9907 | 1.3347 | `2ba339e166e7` |
| 3656 | 29,949,952 | 85,151 | 0.9908 | 1.2544 | `4910def751d1` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.0802794851357691).
- Individual parity ±1% of target: True.
- Host init pack: 85,228 B, fill 0.9917, ratio 0.993510; submitted d_ff 262.
- Estimated compute: 8.812e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4947 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
