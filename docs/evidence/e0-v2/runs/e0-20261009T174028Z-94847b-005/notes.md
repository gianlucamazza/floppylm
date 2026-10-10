# e0-20261009T174028Z-94847b-005

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-005/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 762 | 6,242,304 | 85,595 | 0.9960 | 1.4973 | `5c8bb6adcc70` |
| 1524 | 12,484,608 | 85,639 | 0.9965 | 1.3675 | `d8e9d306c4cb` |
| 3048 | 24,969,216 | 85,410 | 0.9939 | 1.2820 | `38cd943763dc` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08547812053464554).
- Individual parity ±1% of target: True.
- Host init pack: 83,274 B, fill 0.9690, ratio 0.970017; submitted d_ff 205.
- Estimated compute: 6.216e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  2842 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
