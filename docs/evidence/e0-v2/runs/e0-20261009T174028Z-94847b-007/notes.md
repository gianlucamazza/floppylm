# e0-20261009T174028Z-94847b-007

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-007/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 762 | 6,242,304 | 85,649 | 0.9966 | 1.5053 | `f06b773c61b7` |
| 1524 | 12,484,608 | 85,616 | 0.9963 | 1.3785 | `b38e874c54fe` |
| 3048 | 24,969,216 | 85,468 | 0.9945 | 1.2911 | `8faed7c27ff8` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08738368540509778).
- Individual parity ±1% of target: True.
- Host init pack: 83,285 B, fill 0.9691, ratio 0.970145; submitted d_ff 205.
- Estimated compute: 6.216e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  2952 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
