# e0-20261009T174028Z-94847b-006

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-006/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 762 | 6,242,304 | 85,506 | 0.9950 | 1.5021 | `d577f45d400d` |
| 1524 | 12,484,608 | 85,645 | 0.9966 | 1.3737 | `c7abaa2c0add` |
| 3048 | 24,969,216 | 85,653 | 0.9967 | 1.2821 | `5c7286913138` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.09151981632450035).
- Individual parity ±1% of target: True.
- Host init pack: 83,282 B, fill 0.9691, ratio 0.970110; submitted d_ff 205.
- Estimated compute: 6.216e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3118 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
