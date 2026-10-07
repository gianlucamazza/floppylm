# e0-20261004T103838Z-c58a86-105-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-105-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 910 | 7,454,720 | 86,153 | 1.0025 | 1.4837 | `7a853e58ea88` |
| 1820 | 14,909,440 | 85,942 | 1.0001 | 1.3653 | `c606b961bda2` |
| 3640 | 29,818,880 | 85,660 | 0.9968 | 1.2903 | `c680b4371059` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07502416418693758).
- Individual parity ±1% of target: True.
- Estimated compute: 8.823e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5408 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-07)

Eligible after the S3 repair: `d` 112, 3 layers, `d_ff` 192, val bpb 1.4837/1.3653/1.2903.
One grid cell. Not a shape decision.
