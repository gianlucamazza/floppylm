# e0-20261009T174028Z-94847b-003

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-003/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 914 | 7,487,488 | 84,974 | 0.9888 | 1.4638 | `116da43b44d5` |
| 1828 | 14,974,976 | 84,903 | 0.9880 | 1.3489 | `3a97b17b0c66` |
| 3656 | 29,949,952 | 84,756 | 0.9863 | 1.2680 | `62266b006be8` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08083174379859637).
- Individual parity ±1% of target: False.
- Host init pack: 85,236 B, fill 0.9918, ratio 0.993603; submitted d_ff 262.
- Estimated compute: 8.812e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4897 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
