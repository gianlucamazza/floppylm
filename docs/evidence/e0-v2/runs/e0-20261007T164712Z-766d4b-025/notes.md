# e0-20261007T164712Z-766d4b-025

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-025/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 758 | 6,209,536 | 85,546 | 0.9954 | 1.5261 | `dee55deb406e` |
| 1516 | 12,419,072 | 85,573 | 0.9958 | 1.3876 | `5aac746c5356` |
| 3032 | 24,838,144 | 85,591 | 0.9960 | 1.2869 | `c6843b37273d` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.10069546641033034).
- Individual parity ±1% of target: True.
- Host init pack: 83,490 B, fill 0.9715, ratio 0.974576; submitted d_ff 135.
- Estimated compute: 6.612e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4760 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-09)

Eligible on the first pack under ADR 0019 and ADR 0020. One 2-bit grid cell,
`d` 80, 5 layers, submitted `d_ff` 135. Not the 2-bit phase selection.
