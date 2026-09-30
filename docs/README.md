# FloppyLM documentation

Il [README root](../README.md) è la storia pubblica. Questa pagina dice **quale documento possiede
quale fatto**. Aggiornare il documento owner; non copiare tabelle di stato.

## Percorso da 5 minuti

| #   | Domanda                         | Leggi                                                                      |
| --- | ------------------------------- | -------------------------------------------------------------------------- |
| 1   | Qual è la tesi e cosa la uccide | [concept](concept.md)                                                      |
| 2   | Cosa c'è già e cosa no          | [positioning](positioning.md), poi [R2](research/02-procedural-weights.md) |
| 3   | Cosa conta nel budget           | [ADR 0001](adr/0001-floppy-budget.md)                                      |
| 4   | Cosa si misura, in che ordine   | [experiments-roadmap](experiments-roadmap.md)                              |

## Ownership

| Documento                                          | Possiede                          | Non possiede          |
| -------------------------------------------------- | --------------------------------- | --------------------- |
| `README.md` (root)                                 | Storia pubblica, stato, mappa     | F*, definizioni E*    |
| [`vision.md`](vision.md)                           | Mission, successo v0.1, non-goals | Tesi                  |
| [`concept.md`](concept.md)                         | Tesi, principi P1–P4, F0–F4       | Numeri, codice        |
| [`positioning.md`](positioning.md)                 | Confronto con lo stato dell'arte  | Survey complete       |
| [`glossary.md`](glossary.md)                       | Una riga + owner per termine      | Definizioni di record |
| [`stack.md`](stack.md)                             | Toolchain, macchina               | Status, tesi          |
| [`experiments-roadmap.md`](experiments-roadmap.md) | Definizioni E0–E4 e gate          | Risultati             |
| [`adr/`](adr/README.md)                            | Decisioni accettate               | Brainstorm            |
| [`research/`](research/README.md)                  | Letteratura e gap                 | Design normativo      |
| [`evidence/`](evidence/README.md)                  | Numeri misurati                   | Design                |

Vocabolario di stato: **specified** (scritto, non eseguito), **stub**, **running**, **measured**
(un file in `evidence/` possiede il numero), **killed** (un F* è scattato), **won't run**.

## Codice

```
src/floppylm/rans.py      rANS statico, tabella di frequenze dentro lo stream
src/floppylm/quant.py     formati ternary / 2bit / 4bit, scale fp16 per riga, STE
src/floppylm/model.py     TinyGPT: core quantizzato, embedding tied 4 bit, norme fp16
src/floppylm/pack.py      modello ↔ byte del floppy; len(pack) è il conteggio (ADR 0003)
src/floppylm/data.py      TinyStoriesV2: dedup esatta, split per hash, file a byte
experiments/e0_lite.py    E0-lite: --plan / --smoke / --run / --full
tests/                    rANS, quantizzatori, pack, bpb, split, CLI
```
