# e0-20261007T164712Z-766d4b-010

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-010/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 917 | 7,512,064 | 85,969 | 1.0004 | 1.4739 | `31d4518ff414` |
| 1834 | 15,024,128 | 85,954 | 1.0002 | 1.3701 | `460e4974793d` |
| 3668 | 30,048,256 | 85,771 | 0.9981 | 1.2972 | `fdb43709fb9f` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.0729015882772901).
- Individual parity ±1% of target: True.
- Host init pack: 84,698 B, fill 0.9856, ratio 0.986848; submitted d_ff 367.
- Estimated compute: 8.390e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3920 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-08)

Eligible on the first pack under ADR 0019 and ADR 0020. The three cooldown
artifacts match `e0-20261004T103838Z-c58a86-104-repair`. One grid cell of campaign
`e0-20261007T164712Z-766d4b`. Not a shape decision.
