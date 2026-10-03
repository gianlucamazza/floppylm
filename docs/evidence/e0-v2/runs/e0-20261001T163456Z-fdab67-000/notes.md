# e0-20261001T163456Z-fdab67-000

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261001T163456Z-fdab67-000/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 879 | 7,200,768 | 84,793 | 0.9867 | 1.5148 | `b7e7bf4798f2` |
| 1758 | 14,401,536 | 84,916 | 0.9881 | 1.3938 | `e4c829593bc2` |
| 3516 | 28,803,072 | 84,800 | 0.9868 | 1.3120 | `cb6460c937c8` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08184694643023382).
- Individual parity ±1% of target: False.
- Estimated compute: 8.061e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  849 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
