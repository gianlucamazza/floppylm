# e0-20261007T164712Z-766d4b-020

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-020/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 758 | 6,209,536 | 85,259 | 0.9921 | 1.5429 | `2183e60a0c6f` |
| 1516 | 12,419,072 | 85,292 | 0.9925 | 1.3931 | `1105885756c9` |
| 3032 | 24,838,144 | 85,315 | 0.9928 | 1.2898 | `65f852e0e7ee` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.1032616144254197).
- Individual parity ±1% of target: True.
- Host init pack: 83,911 B, fill 0.9764, ratio 0.977323; submitted d_ff 170.
- Estimated compute: 6.547e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4788 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-09)

Eligible on the first pack under ADR 0019 and ADR 0020. One 2-bit grid cell,
`d` 64, 6 layers, submitted `d_ff` 170. Not the 2-bit phase selection.
