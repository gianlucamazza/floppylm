# e0-20261009T174028Z-94847b-000

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-000/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 914 | 7,487,488 | 85,164 | 0.9910 | 1.4654 | `792e7526d818` |
| 1828 | 14,974,976 | 85,105 | 0.9903 | 1.3405 | `e887a3e43cd6` |
| 3656 | 29,949,952 | 85,072 | 0.9899 | 1.2538 | `32fe644bc353` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08669438621354697).
- Individual parity ±1% of target: False.
- Host init pack: 85,223 B, fill 0.9917, ratio 0.993452; submitted d_ff 262.
- Estimated compute: 8.812e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5915 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
