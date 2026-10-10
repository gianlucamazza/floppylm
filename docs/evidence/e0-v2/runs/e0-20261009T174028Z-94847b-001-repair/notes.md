# e0-20261009T174028Z-94847b-001-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261009T174028Z-94847b-001-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 923 | 7,561,216 | 85,975 | 1.0004 | 1.4387 | `01c3e602eec5` |
| 1846 | 15,122,432 | 86,019 | 1.0009 | 1.3272 | `4718b4dfa02c` |
| 3692 | 30,244,864 | 85,801 | 0.9984 | 1.2511 | `9ae412f533dc` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07601494242204865).
- Individual parity ±1% of target: True.
- Estimated compute: 8.975e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5083 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
