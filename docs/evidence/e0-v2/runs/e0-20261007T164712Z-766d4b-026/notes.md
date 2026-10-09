# e0-20261007T164712Z-766d4b-026

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-026/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 768 | 6,291,456 | 85,445 | 0.9943 | 1.5026 | `159c774d8c39` |
| 1536 | 12,582,912 | 85,543 | 0.9954 | 1.3855 | `6f1c26b631dc` |
| 3072 | 25,165,824 | 85,432 | 0.9941 | 1.2982 | `66605f3fabb2` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08730320295865868).
- Individual parity ±1% of target: True.
- Host init pack: 83,218 B, fill 0.9684, ratio 0.968800; submitted d_ff 376.
- Estimated compute: 5.906e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3359 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-09)

Eligible on the first pack under ADR 0019 and ADR 0020. One 2-bit grid cell,
`d` 96, 2 layers, submitted `d_ff` 376. Not the 2-bit phase selection.
