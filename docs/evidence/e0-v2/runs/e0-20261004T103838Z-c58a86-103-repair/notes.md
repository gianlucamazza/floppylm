# e0-20261004T103838Z-c58a86-103-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-103-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 915 | 7,495,680 | 86,175 | 1.0028 | 1.4642 | `5d941194498f` |
| 1830 | 14,991,360 | 86,080 | 1.0017 | 1.3439 | `df82e2676efa` |
| 3660 | 29,982,720 | 85,982 | 1.0005 | 1.2666 | `26d907e1179c` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07723424981343019).
- Individual parity ±1% of target: True.
- Estimated compute: 9.148e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5578 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-07)

Eligible after the S3 repair: `d` 96, 4 layers, `d_ff` 176, val bpb 1.4642/1.3439/1.2666,
85982 bytes at 4T. This is the large end of the grid. Not a shape decision.
