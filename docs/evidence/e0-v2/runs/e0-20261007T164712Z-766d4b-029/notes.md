# e0-20261007T164712Z-766d4b-029

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-029/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 754 | 6,176,768 | 85,932 | 0.9999 | 1.5715 | `521059a59968` |
| 1508 | 12,353,536 | 85,815 | 0.9986 | 1.4461 | `9cc7a688d83c` |
| 3016 | 24,707,072 | 85,743 | 0.9977 | 1.3566 | `1ff4f7d15f30` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08948597488205823).
- Individual parity ±1% of target: True.
- Host init pack: 82,905 B, fill 0.9647, ratio 0.965201; submitted d_ff 189.
- Estimated compute: 5.966e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4472 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-09)

Eligible on the first pack under ADR 0019 and ADR 0020. One 2-bit grid cell,
`d` 128, 2 layers, submitted `d_ff` 189. Not the 2-bit phase selection.
