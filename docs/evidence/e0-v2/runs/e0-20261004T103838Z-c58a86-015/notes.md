# e0-20261004T103838Z-c58a86-015

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-015/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 907 | 7,430,144 | 83,491 | 0.9715 | 1.4741 | `81f0efde19aa` |
| 1814 | 14,860,288 | 83,410 | 0.9706 | 1.3585 | `3c9628cbb0ec` |
| 3628 | 29,720,576 | 83,391 | 0.9704 | 1.2865 | `4a9bee05a874` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07201909297949527).
- Individual parity ±1% of target: False.
- Estimated compute: 8.540e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5252 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-06)

Outside ±1% at nominal `d_ff` 274, lr 0.01, delta 0.7, seed 0. The eligible number is
the S3 repair at `d_ff` 288. This original is not a tuning result.
