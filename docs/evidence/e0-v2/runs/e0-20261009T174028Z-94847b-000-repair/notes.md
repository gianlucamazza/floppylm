# e0-20261009T174028Z-94847b-000-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-000-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 923 | 7,561,216 | 85,804 | 0.9984 | 1.4828 | `75e704bb4c14` |
| 1846 | 15,122,432 | 86,007 | 1.0008 | 1.3632 | `928ac20294cd` |
| 3692 | 30,244,864 | 85,856 | 0.9991 | 1.2788 | `4a9e8b339e4f` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08442830243563693).
- Individual parity ±1% of target: True.
- Estimated compute: 8.975e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5172 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
