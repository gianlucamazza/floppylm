# e0-20261004T103838Z-c58a86-008

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-008/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 913 | 7,479,296 | 84,780 | 0.9865 | 1.4723 | `d095944657ef` |
| 1826 | 14,958,592 | 85,051 | 0.9897 | 1.3578 | `67ff8dcd97b0` |
| 3652 | 29,917,184 | 84,885 | 0.9878 | 1.2701 | `897738ff95f5` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.0876387965134835).
- Individual parity ±1% of target: False.
- Estimated compute: 8.642e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3473 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Outside ±1% at nominal `d_ff` 415. The eligible number is the S3 repair at `d_ff` 424.
This original is not an activation result.
