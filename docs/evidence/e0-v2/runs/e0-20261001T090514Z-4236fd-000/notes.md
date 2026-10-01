# e0-20261001T090514Z-4236fd-000

Stato: **completed**. Configurazione e ambiente completi in `summary.json`; manifest in
`runs/e0-20261001T090514Z-4236fd-000/manifest.json`.

| Fine cooldown (step) | Token visti | Byte | Riempimento | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 879 | 7,200,768 | 84,793 | 0.9867 | 1.5148 | `b7e7bf4798f2` |
| 1758 | 14,401,536 | 84,916 | 0.9881 | 1.3938 | `e4c829593bc2` |
| 3516 | 28,803,072 | 84,800 | 0.9868 | 1.3120 | `cb6460c937c8` |

- Saturazione: non saturo (bpb(4T) − bpb(2T) = -0.08184694643023382).
- Parità individuale ±1% sul target: False.
- Compute stimato: 8.061e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3096 s a 2 thread.

Non misurato qui: test (solo `--final-test` su selezione congelata), σ appaiata, confronto fra
bracci.
