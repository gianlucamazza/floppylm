# E0-lite pre-v2 — diagnostica, esclusa dai verdetti

Due run della griglia scalare a 1/16, fermata il 2026-09-30 perché invalida come confronto
([ADR 0005](../../../adr/0005-e0v2-protocol.md)): riempimento del budget 0.88 vs 0.92 (parità
violata), schedule coseno non saturo, avversario non tarato, test valutato dentro il run.

| Run                     | Byte   | val bpb            | test bpb           | sha256 del blob                                                    |
| ----------------------- | ------ | ------------------ | ------------------ | ------------------------------------------------------------------ |
| `b16-ternary-d64-l6-s0` | 75 942 | 2.0129680935772494 | 2.0154060906348845 | `514991ca5b71a5503f27a9b8991919ef1780089a3519bff43c0ed0beb3e01cf6` |
| `b16-ternary-d80-l4-s0` | 78 627 | 1.8551768137161695 | 1.8632087339879280 | `f32745d175872a0c673ad9eee5f2a9d47232d000c18ce841ccbe5366f93a8baf` |

Smoke dello stesso codice: `runs/smoke/model.flp`, 7 713 B, sha256
`1dfae3659fcd4bfe09e7a43641fe70c251ef5e66dd5ff7e147197fee2f34c79d` (copia in
`tests/fixtures/flp1_smoke.flp`).

## Cosa si sa e cosa no

- I JSON in questa cartella sono l'output originale dell'harness `e0_lite.py`, non modificati.
- I blob stanno in `runs/<tag>/model.flp`, fuori da Git. Sono in formato **`FLP1`, non più
  leggibile dal codice attivo** ([ADR 0006](../../../adr/0006-flp2-only.md)); si leggono alla
  revisione Git `f9e0732`, dove i valori di val bpb qui sopra sono stati riprodotti esattamente.
- Protocollo di valutazione pre-v2: finestre non sovrapposte da 257 byte, primo MiB di val e
  primi 2 MiB di test; contesto 256 byte, tokenizer a byte.
- **Non disponibili**, e non ricostruiti: hash del codice al momento del run (il repo Git non
  esisteva), hash dei file dati usati, ambiente esatto. `experiments/e0_lite.py` alla revisione
  `f9e0732` ha la stessa logica usata per i run (cambiano solo docstring e testi di help), ma lì
  non è più eseguibile: importa `floppylm.quant`, già sostituito da `codec.py`.
