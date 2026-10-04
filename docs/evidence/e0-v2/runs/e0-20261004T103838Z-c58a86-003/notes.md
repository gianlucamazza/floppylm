# e0-20261004T103838Z-c58a86-003

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-003/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 913 | 7,479,296 | 84,811 | 0.9869 | 1.5143 | `b6a120e54c69` |
| 1826 | 14,958,592 | 84,933 | 0.9883 | 1.4011 | `9219940e9323` |
| 3652 | 29,917,184 | 84,888 | 0.9878 | 1.3211 | `4c65d941a669` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.0799335912232293).
- Individual parity ±1% of target: False.
- Estimated compute: 8.642e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3398 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
