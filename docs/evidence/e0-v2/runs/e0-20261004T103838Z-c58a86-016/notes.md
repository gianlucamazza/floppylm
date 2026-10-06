# e0-20261004T103838Z-c58a86-016

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-016/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 915 | 7,495,680 | 85,561 | 0.9956 | 1.4770 | `d909c533ea4d` |
| 1830 | 14,991,360 | 85,531 | 0.9953 | 1.3595 | `e3c8eab80fa6` |
| 3660 | 29,982,720 | 85,500 | 0.9949 | 1.2699 | `9d60cbe96c9a` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08960476140684359).
- Individual parity ±1% of target: True.
- Estimated compute: 9.153e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5637 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-06)

Eligible on the first pack: `d` 64, 6 layers, `d_ff` 226, lr 0.01, delta 0.5, seed 0.
Val bpb 1.4770/1.3595/1.2699. One grid cell. Not a shape decision.
