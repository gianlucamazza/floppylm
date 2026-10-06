# e0-20261004T103838Z-c58a86-014

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-014/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 907 | 7,430,144 | 84,982 | 0.9889 | 1.4582 | `34ed8b00bcf1` |
| 1814 | 14,860,288 | 84,848 | 0.9873 | 1.3376 | `548a5515ea65` |
| 3628 | 29,720,576 | 84,688 | 0.9855 | 1.2554 | `c3d50ee72d16` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08216342478116379).
- Individual parity ±1% of target: False.
- Estimated compute: 8.540e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5246 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-06)

Outside ±1% at nominal `d_ff` 274, lr 0.01, delta 0.5, seed 0. The eligible number is
the S3 repair at `d_ff` 281. This original is not a tuning result.
