# ADR 0003: Pratiche di laboratorio

## Status

Accepted — 2026-09-30. Amended — 2026-09-30.

Superseded in parte da [ADR 0005](0005-e0v2-protocol.md): §2 e §7.

## Context

SmallerGPT ha chiuso due linee perché l'idea esotica non batteva un avversario banale; le
pratiche di [ADR 0004 di SmallerGPT](../../../smallergpt/docs/adr/0004-lab-practices.md) hanno
reso quelle chiusure credibili. Qui il rischio specifico è diverso: **barare sul conteggio dei
byte** (tokenizer "gratis", runtime escluso, seed che nascondono dati).

## Decision

1. Ogni condizione stampa `image_bytes` (totale), `runtime_bytes`, `tokenizer_bytes`,
   `model_bytes`, `effective_params`. Il numero che conta è `image_bytes`, contato sul file
   reale, non stimato.
2. Un confronto fra condizioni con `image_bytes` diversi oltre l'1% è invalido.
3. `seed_all(n)` è l'unico entry point RNG. I seed dei generatori procedurali fanno parte
   della descrizione e si contano nei byte.
4. Evidence = `summary.json` + `notes.md` in `docs/evidence/e<N>-<tag>/`. Senza notes il run non
   è measured.
5. Stop su F*: se F1 scatta in E1, E2–E4 diventano _won't run_ per la tesi procedurale.
6. Harness senza flag → help, exit 2. `--smoke` / `--full` espliciti. Job lunghi: vedi amendment.
7. Split held-out fissato in E0 e mai toccato dal training né dalla scelta di iperparametri.
8. Ruff format+lint su Python; `clang-format` sul runtime C.

## Consequences

- Il bit-accounting è codice testato, non una tabella nei docs.
- Nessun iperparametro si sceglie guardando l'held-out.

## Amendment — 2026-09-30

Il punto 6 cambia su decisione dell'utente: i job di training **non** girano in `background.slice`.
La slice ha una quota fissa di 1 core (`cpu.max 100000 100000`): con 4 thread il training usava
~0.7 core e ogni stima di [R6](../research/06-hardware-budget.md) andava moltiplicata per ~4.
I job partono con `nohup` e log in `runs/*.log`, a 4 thread; il governor termico resta l'unico limite.
