# e0-20261004T103838Z-c58a86-100

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-100/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 907 | 7,430,144 | 85,230 | 0.9918 | 1.4656 | `5cfe7069bcdd` |
| 1814 | 14,860,288 | 85,285 | 0.9924 | 1.3467 | `bd946c0253c5` |
| 3628 | 29,720,576 | 85,123 | 0.9905 | 1.2614 | `09baa11cc7ec` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.0853129983555787).
- Individual parity ±1% of target: True.
- Estimated compute: 9.085e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5590 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-07)

Eligible on the first pack: `d` 80, 5 layers, `d_ff` 186, lr 0.01, delta 0.5, seed 0.
Val bpb 1.4656/1.3467/1.2614. One grid cell. Not a shape decision.
