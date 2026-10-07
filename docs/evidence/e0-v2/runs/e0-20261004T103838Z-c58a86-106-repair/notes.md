# e0-20261004T103838Z-c58a86-106-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-106-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 906 | 7,421,952 | 86,096 | 1.0018 | 1.5380 | `0b49f349c6b3` |
| 1812 | 14,843,904 | 85,819 | 0.9986 | 1.4259 | `c02214d8e2e9` |
| 3624 | 29,687,808 | 85,680 | 0.9970 | 1.3470 | `cb5e8fb5b89a` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07884381582380184).
- Individual parity ±1% of target: True.
- Estimated compute: 8.361e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5281 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-07)

Eligible after the S3 repair: `d` 128, 2 layers, `d_ff` 270, val bpb 1.5380/1.4259/1.3470.
One grid cell. Not a shape decision.
