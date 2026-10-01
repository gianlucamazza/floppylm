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
Summary e note in questa cartella sono versionati: solo `/runs/` alla radice è ignorato.
Le selezioni storiche `smoke-functional*.json`, precedenti ad ADR 0007, restano inalterate.
Le nuove selezioni dichiarano `purpose: scientific | functional`; gli smoke richiedono
`--freeze ... --functional` e non possono certificare una baseline scientifica.

## Presente

| Evidenza                                                                                                                                    | Tipo                                                                 | Stato       |
| ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ----------- |
| [`e0-v2/runs/smoke-ternary-d32-l1-f48-s0-20260930T081747Z-973ccb`](e0-v2/runs/smoke-ternary-d32-l1-f48-s0-20260930T081747Z-973ccb/notes.md) | smoke, **prova funzionale, non scientifica**                         | completed   |
| `e0-v2/runs/smoke-ternary-d32-l1-f48-s0-20260930T081826Z-e393da`                                                                            | test del percorso SIGTERM, smoke interrotto apposta                  | interrupted |
| `e0-v2/selections/smoke-functional*.json`                                                                                                   | prova funzionale di `--freeze` / `--final-test` sullo smoke          | —           |
| [`e0-lite/pre-v2`](e0-lite/pre-v2/notes.md)                                                                                                 | griglia E0-lite fermata; diagnostica esclusa dai verdetti, blob FLP1 | —           |

## Xbox execution evidence

[Current package acceptance](xbox-e0-20261001/notes.md) owns the measured GPU parity,
throughput, memory, real suspension and recovery results. Earlier evidence remains
unchanged as a historical record, including failed baselines.

Scientific E0 results remain pending. S1–S10 and the row16/row8log decision are
accepted; the [roadmap](../experiments-roadmap.md) defines completion gates.
Campaign reports appear under `e0-v2/campaigns/<campaign_id>/`; the local durable
manifest and trial logs are under `runs/e0-campaign-20261001/`.

## Isolated E1 qualification

[CPU functional qualification](e1-qualification-20261001/notes.md) records scalar
profiling, BPE512 round trips, vector book/byte probes and deterministic partial
quantization canaries under ADR 0013. It is neither scientific E1 nor Xbox vector
acceptance; the current E0.1 campaign directory is `runs/e0-campaign-20261001-e01/`.
