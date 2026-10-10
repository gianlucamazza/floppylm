# e0-20261009T174028Z-94847b-003-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-003-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 928 | 7,602,176 | 86,340 | 1.0047 | 1.4557 | `3e05108c3ae7` |
| 1856 | 15,204,352 | 86,338 | 1.0047 | 1.3367 | `00acdc2852e3` |
| 3712 | 30,408,704 | 86,261 | 1.0038 | 1.2557 | `ec9453ef9afc` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08097861684958074).
- Individual parity ±1% of target: True.
- Estimated compute: 9.060e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5031 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
