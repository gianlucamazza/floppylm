# e0-20261004T103838Z-c58a86-106

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-106/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 887 | 7,266,304 | 84,414 | 0.9823 | 1.5430 | `610e40125ef0` |
| 1774 | 14,532,608 | 84,303 | 0.9810 | 1.4146 | `d262a8bed4b5` |
| 3548 | 29,065,216 | 84,264 | 0.9805 | 1.3318 | `48aa6c52e8ab` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08278648456955229).
- Individual parity ±1% of target: False.
- Estimated compute: 8.041e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5190 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-07)

Outside ±1% at nominal `d_ff` 260, `d` 128, 2 layers, lr 0.01, delta 0.5, seed 0.
The eligible number is the S3 repair at `d_ff` 270. This original is not a grid result.
