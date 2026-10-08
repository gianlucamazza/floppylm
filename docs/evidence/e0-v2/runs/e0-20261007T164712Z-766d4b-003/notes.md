# e0-20261007T164712Z-766d4b-003

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-003/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 902 | 7,389,184 | 85,833 | 0.9988 | 1.5024 | `24988a29517a` |
| 1804 | 14,778,368 | 85,810 | 0.9985 | 1.3761 | `09bfda26afcb` |
| 3608 | 29,556,736 | 85,812 | 0.9985 | 1.2856 | `a77944b8147b` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.09053567267759788).
- Individual parity ±1% of target: True.
- Host init pack: 85,969 B, fill 1.0004, ratio 1.000455; submitted d_ff 119.
- Estimated compute: 9.853e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  7229 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-08)

Eligible on the first pack under ADR 0019 and ADR 0020. The three cooldown
artifacts match `e0-20261004T103838Z-c58a86-019`. One grid cell of campaign `e0-20261007T164712Z-766d4b`.
Not a shape decision.
