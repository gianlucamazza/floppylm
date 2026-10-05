# e0-20261004T103838Z-c58a86-006-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-006-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 920 | 7,536,640 | 85,917 | 0.9998 | 1.4568 | `5ca415fc6172` |
| 1840 | 15,073,280 | 85,913 | 0.9997 | 1.3403 | `251cefa26792` |
| 3680 | 30,146,560 | 85,989 | 1.0006 | 1.2615 | `f6f1b391e2c3` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07883648990068237).
- Individual parity ±1% of target: True.
- Estimated compute: 8.766e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4677 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Eligible at `d_ff` 280. Val bpb 1.4568/1.3403/1.2615 is seed 0 only. It is lower than
the gelu pair at T, 2T and 4T and is not an activation selection. Seed 1 is a separate
trial.
