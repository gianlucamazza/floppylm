# e0-20261001T090514Z-4236fd-001

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261001T090514Z-4236fd-001/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 879 | 7,200,768 | 84,993 | 0.9890 | 1.5273 | `087c92c153ac` |
| 1758 | 14,401,536 | 84,966 | 0.9887 | 1.4052 | `7aa833f46551` |
| 3516 | 28,803,072 | 84,827 | 0.9871 | 1.3204 | `116e7643ec37` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08478091969375146).
- Individual parity ±1% of target: False.
- Estimated compute: 8.061e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3267 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.
