# Evidence

Questa cartella possiede i **numeri**. Un claim che dice "funziona" senza un file qui è teatro.

Formato di un run E0 v2 ([ADR 0005](../adr/0005-e0v2-protocol.md)):

```
evidence/e0-v2/runs/<run_id>/
  summary.json     # stato, config, byte e hash per cooldown, val bpb, saturazione, compute
  notes.md         # una pagina generata: setup, risultati, cosa non si è misurato
evidence/e0-v2/selections/<name>.json       # selezione congelata con hash degli artefatti
evidence/e0-v2/selections/<name>.test.json  # test finale, una sola volta per selezione
```

Manifest completo, stato e artefatti di ogni run stanno in `runs/<run_id>/` (fuori da Git).

## Presente

| Evidenza                                                                                                                                    | Tipo                                                                 | Stato       |
| ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ----------- |
| [`e0-v2/runs/smoke-ternary-d32-l1-f48-s0-20260930T081747Z-973ccb`](e0-v2/runs/smoke-ternary-d32-l1-f48-s0-20260930T081747Z-973ccb/notes.md) | smoke, **prova funzionale, non scientifica**                         | completed   |
| `e0-v2/runs/smoke-ternary-d32-l1-f48-s0-20260930T081826Z-e393da`                                                                            | test del percorso SIGTERM, smoke interrotto apposta                  | interrupted |
| `e0-v2/selections/smoke-functional*.json`                                                                                                   | prova funzionale di `--freeze` / `--final-test` sullo smoke          | —           |
| [`e0-lite/pre-v2`](e0-lite/pre-v2/notes.md)                                                                                                 | griglia E0-lite fermata; diagnostica esclusa dai verdetti, blob FLP1 | —           |

Nessun risultato scientifico E0 v2: la campagna non è partita (scelte S1–S10 da approvare,
[roadmap](../experiments-roadmap.md#e0-v2--scelte-da-approvare)).
