# e0-20261007T164712Z-766d4b-028

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-028/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 761 | 6,234,112 | 85,717 | 0.9974 | 1.5419 | `ef1c52f855ed` |
| 1522 | 12,468,224 | 85,685 | 0.9971 | 1.4220 | `6a161e035199` |
| 3044 | 24,936,448 | 85,634 | 0.9965 | 1.3377 | `fecf367043fe` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08424203263442331).
- Individual parity ±1% of target: True.
- Host init pack: 82,952 B, fill 0.9653, ratio 0.966829; submitted d_ff 272.
- Estimated compute: 5.937e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3374 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-09)

Eligible on the first pack under ADR 0019 and ADR 0020. One 2-bit grid cell,
`d` 112, 2 layers, submitted `d_ff` 272. Not the 2-bit phase selection.
