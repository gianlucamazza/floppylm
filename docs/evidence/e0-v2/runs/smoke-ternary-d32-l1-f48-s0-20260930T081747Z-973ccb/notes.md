# smoke-ternary-d32-l1-f48-s0-20260930T081747Z-973ccb

**Smoke: prova funzionale, non un risultato scientifico.**

Stato: **completed**. Configurazione e ambiente completi in `summary.json`; manifest in
`runs/smoke-ternary-d32-l1-f48-s0-20260930T081747Z-973ccb/manifest.json`.

| Fine cooldown (step) | Token visti | Byte | Riempimento | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 16 | 8,192 | 6,519 | 0.0759 | 5.1353 | `47a8226becb1` |
| 32 | 16,384 | 6,515 | 0.0758 | 4.3818 | `587aa5d21f81` |

- Saturazione: non determinato (meno di 3 cooldown) (bpb(4T) − bpb(2T) = None).
- Parità individuale ±1% sul target: False.
- Compute stimato: 1.765e+09 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3 s a 4 thread.

Non misurato qui: test (solo `--final-test` su selezione congelata), σ appaiata, confronto fra
bracci.
