# e0-20261004T103838Z-c58a86-004-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-004-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 926 | 7,585,792 | 85,852 | 0.9990 | 1.5039 | `0ca43c5d18bb` |
| 1852 | 15,171,584 | 86,088 | 1.0018 | 1.3837 | `94effcc93f99` |
| 3704 | 30,343,168 | 85,969 | 1.0004 | 1.3047 | `236cd31d6ff7` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07900326163836913).
- Individual parity ±1% of target: True.
- Estimated compute: 8.866e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3336 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-04)

The three branch artifact hashes match
`e0-20261004T103838Z-c58a86-002-repair`. Eligible parity here repeats that
scale repair (`d_ff` 424). It is not an activation comparison.
