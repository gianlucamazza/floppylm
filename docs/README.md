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
src/floppylm/codec.py     ScalarCodec: ternary / 2bit / 4bit, scale row16 | row8log | tensor16
src/floppylm/rans.py      rANS 15 bit e bitpack, scelta del più corto per tensore, errori espliciti
src/floppylm/model.py     GPTConfig validata, TinyGPT, bit nominali e FLOP per token
src/floppylm/pack.py      FLP2 ↔ modello; pack(unpack(b)) == b; FLP1 rifiutato (ADR 0006)
src/floppylm/shapes.py    solver di forma: d, n_layers, d_ff libero a 99.5–100% del budget
src/floppylm/train.py     WSD con tronco e cooldown, checkpoint, valutazione scorrevole
src/floppylm/parity.py    ammissibilità sui byte serializzati, σ appaiata
src/floppylm/runlog.py    id univoci, directory esclusive, scritture atomiche, stato, manifest
src/floppylm/data.py      TinyStoriesV2: dedup esatta, split per hash, manifest, riproducibilità
experiments/e0_v2.py      --plan / --run / --grid / --parity / --freeze / --final-test / --verify-data
tests/                    regressioni di tutti i moduli, fixture FLP1 per il test di rifiuto
```
