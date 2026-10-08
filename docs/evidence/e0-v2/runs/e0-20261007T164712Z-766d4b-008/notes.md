# e0-20261007T164712Z-766d4b-008

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-008/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 918 | 7,520,256 | 85,757 | 0.9979 | 1.4667 | `d865a63c545d` |
| 1836 | 15,040,512 | 85,849 | 0.9990 | 1.3477 | `c934e9563e87` |
| 3672 | 30,081,024 | 85,695 | 0.9972 | 1.2654 | `33be395773f7` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08234655500638488).
- Individual parity ±1% of target: True.
- Host init pack: 84,958 B, fill 0.9886, ratio 0.990063; submitted d_ff 279.
- Estimated compute: 8.727e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5351 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-08)

Eligible on the first pack under ADR 0019 and ADR 0020. Init pack submitted
`d_ff` 279. The three cooldown artifacts differ from
`e0-20261004T103838Z-c58a86-102` (`d_ff` 274) and from
`e0-20261004T103838Z-c58a86-102-repair` (`d_ff` 281). One grid cell of campaign
`e0-20261007T164712Z-766d4b`. Not a shape decision.
