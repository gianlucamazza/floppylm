# e0-20261007T164712Z-766d4b-012

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-012/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 904 | 7,405,568 | 85,898 | 0.9995 | 1.5110 | `dad6adbe6bfc` |
| 1808 | 14,811,136 | 85,723 | 0.9975 | 1.3989 | `72cdab343879` |
| 3616 | 29,622,272 | 85,535 | 0.9953 | 1.3215 | `2aacdbd05538` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07745256860012462).
- Individual parity ±1% of target: True.
- Host init pack: 84,464 B, fill 0.9829, ratio 0.984582; submitted d_ff 269.
- Estimated compute: 8.327e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5272 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-08)

Eligible on the first pack under ADR 0019 and ADR 0020. Init pack submitted
`d_ff` 269. The three cooldown artifacts differ from
`e0-20261004T103838Z-c58a86-106` (`d_ff` 260) and from
`e0-20261004T103838Z-c58a86-106-repair` (`d_ff` 270). One grid cell of campaign
`e0-20261007T164712Z-766d4b`. Not the ternary phase selection.
