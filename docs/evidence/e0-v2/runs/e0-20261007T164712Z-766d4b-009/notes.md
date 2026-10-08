# e0-20261007T164712Z-766d4b-009

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-009/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 909 | 7,446,528 | 85,648 | 0.9966 | 1.4681 | `5f09153cde65` |
| 1818 | 14,893,056 | 85,668 | 0.9969 | 1.3507 | `9ab0e8cf94c7` |
| 3636 | 29,786,112 | 85,363 | 0.9933 | 1.2641 | `5637c2a38b43` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.0866241210620784).
- Individual parity ±1% of target: True.
- Host init pack: 85,066 B, fill 0.9899, ratio 0.991028; submitted d_ff 174.
- Estimated compute: 9.041e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5560 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-08)

Eligible on the first pack under ADR 0019 and ADR 0020. Init pack submitted
`d_ff` 174. The three cooldown artifacts differ from
`e0-20261004T103838Z-c58a86-103` (`d_ff` 171) and from
`e0-20261004T103838Z-c58a86-103-repair` (`d_ff` 176). One grid cell of campaign
`e0-20261007T164712Z-766d4b`. Not a shape decision.
