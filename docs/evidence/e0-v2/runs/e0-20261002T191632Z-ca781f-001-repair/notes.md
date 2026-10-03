# e0-20261002T191632Z-ca781f-001-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261002T191632Z-ca781f-001-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 892 | 7,307,264 | 85,904 | 0.9996 | 1.5100 | `4d2151d7e601` |
| 1784 | 14,614,528 | 86,000 | 1.0007 | 1.3916 | `42db3e2c1641` |
| 3568 | 29,229,056 | 86,015 | 1.0009 | 1.3082 | `9901d9d431f8` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08342740803625803).
- Individual parity ±1% of target: True.
- Estimated compute: 8.281e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3170 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
