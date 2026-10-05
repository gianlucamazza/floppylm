# e0-20261004T103838Z-c58a86-009-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-009-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 924 | 7,569,408 | 85,828 | 0.9987 | 1.4790 | `94b86d769951` |
| 1848 | 15,138,816 | 85,892 | 0.9995 | 1.3679 | `728c8d0b6912` |
| 3696 | 30,277,632 | 85,947 | 1.0001 | 1.2837 | `1c1b41d76d41` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08413650457649302).
- Individual parity ±1% of target: True.
- Estimated compute: 8.835e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3465 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Eligible S3 repair, `d_ff` 423. Val bpb 1.4790/1.3679/1.2837 is ReLU² seed 1.
With seed 0 the mean is 1.4770/1.3638/1.2822, below gelu and above SwiGLU at T, 2T and 4T.
Neutral MLP selected SwiGLU at nominal `d_ff` 274.
