# e0-20261001T090514Z-4236fd-001

Stato: **completed**. Configurazione e ambiente completi in `summary.json`; manifest in
`runs/e0-20261001T090514Z-4236fd-001/manifest.json`.

| Fine cooldown (step) | Token visti | Byte | Riempimento | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 879 | 7,200,768 | 84,993 | 0.9890 | 1.5273 | `087c92c153ac` |
| 1758 | 14,401,536 | 84,966 | 0.9887 | 1.4052 | `7aa833f46551` |
| 3516 | 28,803,072 | 84,827 | 0.9871 | 1.3204 | `116e7643ec37` |

- Saturazione: non saturo (bpb(4T) − bpb(2T) = -0.08478091969375146).
- Parità individuale ±1% sul target: False.
- Compute stimato: 8.061e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3267 s a 2 thread.

Non misurato qui: test (solo `--final-test` su selezione congelata), σ appaiata, confronto fra
bracci.
