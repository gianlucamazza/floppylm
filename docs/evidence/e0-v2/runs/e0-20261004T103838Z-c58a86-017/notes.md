# e0-20261004T103838Z-c58a86-017

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-017/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 910 | 7,454,720 | 85,648 | 0.9966 | 1.4744 | `5ad1d426d7af` |
| 1820 | 14,909,440 | 85,689 | 0.9971 | 1.3591 | `4eb813796423` |
| 3640 | 29,818,880 | 85,554 | 0.9955 | 1.2788 | `35cebf88a486` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08025213950080867).
- Individual parity ±1% of target: True.
- Estimated compute: 9.380e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  7071 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-06)

Eligible on the first pack: `d` 64, 7 layers, `d_ff` 180, lr 0.01, delta 0.5, seed 0.
Val bpb 1.4744/1.3591/1.2788. One grid cell. Not a shape decision.
