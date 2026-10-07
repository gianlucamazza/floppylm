# e0-20261004T103838Z-c58a86-104

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-104/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 902 | 7,389,184 | 84,702 | 0.9856 | 1.4862 | `62184ea2e671` |
| 1804 | 14,778,368 | 84,713 | 0.9858 | 1.3761 | `189335ddd4ed` |
| 3608 | 29,556,736 | 84,600 | 0.9844 | 1.3023 | `741cdd1c3511` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07380044043033629).
- Individual parity ±1% of target: False.
- Estimated compute: 8.138e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3871 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-07)

Outside ±1% at nominal `d_ff` 358, `d` 112, 2 layers, lr 0.01, delta 0.5, seed 0.
The eligible number is the S3 repair at `d_ff` 367. This original is not a grid result.
