# e0-20261004T103838Z-c58a86-007

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-007/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 907 | 7,430,144 | 84,871 | 0.9876 | 1.4642 | `695155822998` |
| 1814 | 14,860,288 | 84,882 | 0.9877 | 1.3546 | `2a9ed5ef5665` |
| 3628 | 29,720,576 | 84,848 | 0.9873 | 1.2748 | `5924d506892c` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07987113106737076).
- Individual parity ±1% of target: False.
- Estimated compute: 8.540e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4666 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Outside ±1% at nominal `d_ff` 274. The eligible number is the S3 repair at `d_ff` 280.
This original is not an activation result.
