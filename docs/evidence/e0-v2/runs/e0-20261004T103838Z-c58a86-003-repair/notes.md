# e0-20261004T103838Z-c58a86-003-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-003-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 926 | 7,585,792 | 85,939 | 1.0000 | 1.5112 | `9d530903f582` |
| 1852 | 15,171,584 | 85,956 | 1.0002 | 1.3876 | `b5c87fcde8ea` |
| 3704 | 30,343,168 | 85,821 | 0.9986 | 1.3070 | `b217b0fdae0a` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08058458323457107).
- Individual parity ±1% of target: True.
- Estimated compute: 8.866e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3448 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
