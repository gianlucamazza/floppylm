# e0-20261004T103838Z-c58a86-022-r3

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-022-r3/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 914 | 7,487,488 | 85,288 | 0.9924 | 1.4599 | `f67b5c5d0346` |
| 1828 | 14,974,976 | 85,185 | 0.9912 | 1.3375 | `a4c92e422922` |
| 3656 | 29,949,952 | 85,098 | 0.9902 | 1.2522 | `0c1a4a8ff18e` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08531008553573716).
- Individual parity ±1% of target: True.
- Estimated compute: 8.812e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5527 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-07)

Eligible on the first pack: `d` 80, 4 layers, `d_ff` 262, lr 0.01, delta 0.5, seed 0.
Val bpb 1.4599/1.3375/1.2522, 85098 bytes at 4T. This is the small end of the grid.
Trials `021` and `022` failed before a branch and are not results. Not a shape decision.
