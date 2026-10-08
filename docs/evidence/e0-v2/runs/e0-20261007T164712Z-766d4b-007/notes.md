# e0-20261007T164712Z-766d4b-007

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-007/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 903 | 7,397,376 | 85,452 | 0.9944 | 1.4906 | `cd6ee0bdd666` |
| 1806 | 14,794,752 | 85,406 | 0.9938 | 1.3699 | `6fb257e4e806` |
| 3612 | 29,589,504 | 85,312 | 0.9927 | 1.2764 | `59277d9d0bd2` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.093515298156853).
- Individual parity ±1% of target: True.
- Host init pack: 85,491 B, fill 0.9948, ratio 0.995364; submitted d_ff 136.
- Estimated compute: 9.403e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3029 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-08)

Eligible on the first pack under ADR 0019 and ADR 0020. The three cooldown
artifacts match `e0-20261004T103838Z-c58a86-101`. One grid cell of campaign `e0-20261007T164712Z-766d4b`.
Not a shape decision.
