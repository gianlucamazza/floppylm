# e0-20261009T174028Z-94847b-002

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-002/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 914 | 7,487,488 | 85,192 | 0.9913 | 1.4662 | `d60343de09d0` |
| 1828 | 14,974,976 | 85,139 | 0.9907 | 1.3496 | `ea4850874034` |
| 3656 | 29,949,952 | 85,130 | 0.9906 | 1.2704 | `47b3a41638e3` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.0791565596945003).
- Individual parity ±1% of target: True.
- Host init pack: 85,214 B, fill 0.9916, ratio 0.993347; submitted d_ff 262.
- Estimated compute: 8.812e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4913 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
