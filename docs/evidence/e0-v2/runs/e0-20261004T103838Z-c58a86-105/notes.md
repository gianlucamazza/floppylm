# e0-20261004T103838Z-c58a86-105

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-105/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 892 | 7,307,264 | 84,640 | 0.9849 | 1.4972 | `182817beeadd` |
| 1784 | 14,614,528 | 84,486 | 0.9831 | 1.3798 | `30f7c7a08d3d` |
| 3568 | 29,229,056 | 84,357 | 0.9816 | 1.3020 | `c56b92167716` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07778342034080388).
- Individual parity ±1% of target: False.
- Estimated compute: 8.514e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5310 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-07)

Outside ±1% at nominal `d_ff` 185, `d` 112, 3 layers, lr 0.01, delta 0.5, seed 0.
The eligible number is the S3 repair at `d_ff` 192. This original is not a grid result.
