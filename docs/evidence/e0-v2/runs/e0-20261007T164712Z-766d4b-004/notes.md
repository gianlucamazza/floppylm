# e0-20261007T164712Z-766d4b-004

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-004/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 894 | 7,323,648 | 85,836 | 0.9988 | 1.5183 | `707e3f5fb989` |
| 1788 | 14,647,296 | 85,708 | 0.9973 | 1.3945 | `30e394ee9a0a` |
| 3576 | 29,294,592 | 85,689 | 0.9971 | 1.3089 | `a6fba52a537d` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08556767052936953).
- Individual parity ±1% of target: True.
- Host init pack: 85,836 B, fill 0.9988, ratio 1.001400; submitted d_ff 97.
- Estimated compute: 1.002e+14 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  8408 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-08)

Eligible on the first pack under ADR 0019 and ADR 0020. The three cooldown
artifacts match `e0-20261004T103838Z-c58a86-020`. One grid cell of campaign `e0-20261007T164712Z-766d4b`.
Not a shape decision.
