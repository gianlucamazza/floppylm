# e0-20261004T103838Z-c58a86-010

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-010/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 907 | 7,430,144 | 84,527 | 0.9836 | 1.5810 | `bf3c1dc46f95` |
| 1814 | 14,860,288 | 84,753 | 0.9862 | 1.4346 | `2eeeec503873` |
| 3628 | 29,720,576 | 84,934 | 0.9883 | 1.3351 | `747580592178` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.09948734854587205).
- Individual parity ±1% of target: False.
- Estimated compute: 8.540e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4993 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Outside ±1% at nominal `d_ff` 274, lr 0.001, delta 0.5, seed 0. The eligible number is
the S3 repair at `d_ff` 279. This original is not a tuning result.
