# e0-20261009T174028Z-94847b-009

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-009/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 762 | 6,242,304 | 85,620 | 0.9963 | 1.5142 | `0af2a096717b` |
| 1524 | 12,484,608 | 85,694 | 0.9972 | 1.3858 | `36f5e8d0c7bc` |
| 3048 | 24,969,216 | 85,575 | 0.9958 | 1.2927 | `34a221067b0c` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.09307851165468106).
- Individual parity ±1% of target: True.
- Host init pack: 83,253 B, fill 0.9688, ratio 0.969772; submitted d_ff 205.
- Estimated compute: 6.216e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  2991 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
