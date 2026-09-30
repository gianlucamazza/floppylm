# Vision

## Mission

Il miglior language model che stia su un floppy 3.5" reale, misurato in qualità per byte, e la
risposta misurata a una domanda aperta: sotto il bit, da zero, un codice vettoriale nel core batte
il ternario, e il codice va appreso o basta generarlo?

## Successo v0.1

- E0–E2 **measured**, con F1 e F2 decisi in un verso o nell'altro.
- Se la tesi regge: E4 produce un'immagine da 1 474 560 B che genera storie TinyStories coerenti.
- Se non regge: la frontiera bpb-per-byte sotto 1.5 MB (scalare vs vettoriale, con e senza
  ricorsione) è comunque pubblicabile.

## Non-goals

- Conoscenza fattuale, chat, istruzioni.
- Floppy bootabile: floppy dati eseguito da host Linux ([ADR 0001](adr/0001-floppy-budget.md)).
- Battere modelli fuori budget; SmolLM2 è solo un riferimento di scala.
