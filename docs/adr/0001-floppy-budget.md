# ADR 0001: Il budget è il floppy, non i parametri

## Status

Accepted — 2026-09-30.

## Context

Il nome `floppy_4mb` è simbolico: il target è un floppy 3.5" HD reale,
2880 settori da 512 B = 1 474 560 B. Senza una regola di conteggio scritta prima di E0, ogni
confronto è truccabile (tokenizer fuori budget, runtime "di sistema", librerie dinamiche).

Misure in [R4](../research/04-runtime-and-demoscene.md): FAT12 costa 33 settori (boot, 2×9 FAT,
14 root dir) → **area dati 1 457 664 B**. `run.c` di llama2.c a `-Os` stripped pesa ~19 KB
dinamico; statico glibc ~0.9 MB (inusabile); musl stimato 30–60 KB. Un floppy Linux bootabile
lascia ~264 KB liberi.

## Decision

1. **Budget** = somma dei file sull'immagine FAT12, arrotondati al cluster da 512 B,
   ≤ 1 457 664 B. Nessun file fuori immagine è richiesto per generare testo, eccetto il kernel
   e la libc dell'host se il binario è dinamico (vedi 3).
2. **Cosa conta**: descrizione del modello (pesi, seed, coefficienti, tabelle di entropy
   coding), tokenizer, binario di runtime, qualsiasi file di configurazione.
3. **Cosa non conta**: l'host (Linux x86-64). Il runtime finale (E4) è un binario **statico
   musl**; fino a E4 si usa una costante pessimistica di 64 KB per runtime + decoder.
4. **Floppy dati, non bootabile.** Il boot è l'esecuzione del binario dal floppy montato.
5. **Budget di boot** (F3): espansione ≤ 60 s, RAM ≤ 1 GB, generazione ≥ 5 tok/s su
   i7-1165G7 a 4 thread, misurati sul binario C, non su PyTorch.
6. Budget operativo per il modello fino a E4: **1 457 664 − 64 KB − tokenizer reale** byte.

## Consequences

- La RAM a runtime è libera fino a 1 GB: è l'asimmetria che la tesi sfrutta
  ([concept](../concept.md)).
- Il tokenizer entra nel budget: vocabolari grandi costano due volte (file + embedding).
