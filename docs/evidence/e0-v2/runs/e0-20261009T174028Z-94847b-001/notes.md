# e0-20261009T174028Z-94847b-001

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-001/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 914 | 7,487,488 | 85,047 | 0.9896 | 1.4471 | `7dcbed23b0fe` |
| 1828 | 14,974,976 | 85,118 | 0.9905 | 1.3341 | `96fe49ec7938` |
| 3656 | 29,949,952 | 84,999 | 0.9891 | 1.2522 | `51f378f276c1` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08196214622265852).
- Individual parity ±1% of target: False.
- Host init pack: 85,219 B, fill 0.9916, ratio 0.993405; submitted d_ff 262.
- Estimated compute: 8.812e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5240 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
