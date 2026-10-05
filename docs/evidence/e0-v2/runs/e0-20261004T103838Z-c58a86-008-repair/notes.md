# e0-20261004T103838Z-c58a86-008-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-008-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 926 | 7,585,792 | 85,829 | 0.9987 | 1.4749 | `4062e2da2358` |
| 1852 | 15,171,584 | 86,048 | 1.0013 | 1.3597 | `03fb0b9acac2` |
| 3704 | 30,343,168 | 85,978 | 1.0005 | 1.2807 | `0b7e3f5a4218` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07899705314955119).
- Individual parity ±1% of target: True.
- Estimated compute: 8.866e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3505 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Eligible S3 repair, `d_ff` 424. Val bpb 1.4749/1.3597/1.2807 is ReLU² seed 0.
It is lower than the gelu pair and higher than both SwiGLU seeds at T, 2T and 4T.
One seed is not a selection.
