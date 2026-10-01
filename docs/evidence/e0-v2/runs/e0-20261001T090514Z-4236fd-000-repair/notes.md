# e0-20261001T090514Z-4236fd-000-repair

Stato: **completed**. Configurazione e ambiente completi in `summary.json`; manifest in
`runs/e0-20261001T090514Z-4236fd-000-repair/manifest.json`.

| Fine cooldown (step) | Token visti | Byte | Riempimento | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 892 | 7,307,264 | 85,850 | 0.9990 | 1.5155 | `65f5addc2416` |
| 1784 | 14,614,528 | 85,922 | 0.9998 | 1.3951 | `f098271a1884` |
| 3568 | 29,229,056 | 86,038 | 1.0012 | 1.3160 | `013a59be8ee9` |

- Saturazione: non saturo (bpb(4T) − bpb(2T) = -0.07907501984609122).
- Parità individuale ±1% sul target: True.
- Compute stimato: 8.281e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3014 s a 2 thread.

Non misurato qui: test (solo `--final-test` su selezione congelata), σ appaiata, confronto fra
bracci.
