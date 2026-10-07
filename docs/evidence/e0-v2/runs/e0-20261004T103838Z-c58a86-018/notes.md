# e0-20261004T103838Z-c58a86-018

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-018/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 903 | 7,397,376 | 85,493 | 0.9948 | 1.4789 | `fdcdf5a824f5` |
| 1806 | 14,794,752 | 85,599 | 0.9961 | 1.3666 | `452fbfab22f1` |
| 3612 | 29,589,504 | 85,520 | 0.9951 | 1.2764 | `6b429d6f8338` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.09021107093086655).
- Individual parity ±1% of target: True.
- Estimated compute: 9.564e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  7075 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-07)

Eligible on the first pack: `d` 64, 8 layers, `d_ff` 145, lr 0.01, delta 0.5, seed 0.
Val bpb 1.4789/1.3666/1.2764. One grid cell. Not a shape decision.
