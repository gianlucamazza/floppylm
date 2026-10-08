# e0-20261007T164712Z-766d4b-011

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-011/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 907 | 7,430,144 | 85,985 | 1.0006 | 1.5020 | `108efadf3f20` |
| 1814 | 14,860,288 | 85,760 | 0.9979 | 1.3799 | `c0bb667c067a` |
| 3628 | 29,720,576 | 85,780 | 0.9982 | 1.3022 | `122d03819e83` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07769406806228552).
- Individual parity ±1% of target: True.
- Host init pack: 84,698 B, fill 0.9856, ratio 0.987799; submitted d_ff 191.
- Estimated compute: 8.772e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5377 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-08)

Eligible on the first pack under ADR 0019 and ADR 0020. Init pack submitted
`d_ff` 191. The three cooldown artifacts differ from
`e0-20261004T103838Z-c58a86-105` (`d_ff` 185) and from
`e0-20261004T103838Z-c58a86-105-repair` (`d_ff` 192). One grid cell of campaign
`e0-20261007T164712Z-766d4b`. Not the ternary phase selection.
