# e0-20261009T174028Z-94847b-008

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-008/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 762 | 6,242,304 | 85,797 | 0.9984 | 1.4925 | `3ca9ce7e911b` |
| 1524 | 12,484,608 | 85,693 | 0.9972 | 1.3665 | `335fc050a508` |
| 3048 | 24,969,216 | 85,576 | 0.9958 | 1.2801 | `05a9f504dfaa` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08637215915018359).
- Individual parity ±1% of target: True.
- Host init pack: 83,297 B, fill 0.9693, ratio 0.970285; submitted d_ff 205.
- Estimated compute: 6.216e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  2902 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
