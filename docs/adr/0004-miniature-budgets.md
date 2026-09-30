# ADR 0004: Floppy in miniatura come proxy di convergenza

## Status

Accepted — 2026-09-30. Amended — 2026-09-30.

## Context

Il prodotto ha byte fissi e training illimitato; il lab ha una CPU
([R6](../research/06-hardware-budget.md)): ~87M token/notte a 5M param, ~8M a 30M. A 1.44 MB i
bracci ricorsivi e sotto il bit restano sotto-allenati di 10–100×, e un "vince il denso" sarebbe
un falso negativo dovuto al compute del lab, non ai byte del floppy.

## Decision

1. E0–E1 si eseguono a **tre budget**: 1/16, 1/4 e 1× di 11 Mbit (≈ 86 KB, 344 KB, 1.38 MB di
   modello). Ai due budget piccoli ogni braccio deve arrivare vicino a saturazione
   (≥ 20 token per parametro stoccato e curva di loss piatta sull'ultimo 10% del training).
2. Un verdetto F1 richiede lo stesso segno ai due budget piccoli e un trend che non si chiude
   salendo di budget. Il punto 1× su CPU è indicativo, non decisivo.
3. La scala piena a convergenza si esegue solo su GPU a noleggio, con un ADR dedicato che fissa
   costo e run.

## Consequences

- La tesi si decide su CPU prima di spendere.
- Un effetto che esiste solo a 1× e non ai budget piccoli non basta a passare F1.

## Amendment — 2026-09-30

1. **Solo byte del modello.** Runtime (~64 KB) e tokenizer sono costanti e a 1/16 varrebbero quasi
   quanto il modello: ai budget in miniatura si confrontano solo i byte codificati del modello.
   L'immagine intera conta solo a 1×.
2. **Proporzioni costanti.** Vocab e larghezza si scelgono per budget in modo che l'embedding resti
   ~15% dei bit: a 1/16 un vocab da 1024 ne prenderebbe il 76%. Tokenizer a byte (V=256) a 1/16 e
   1/4; BPE si valuta solo a 1×. Il bpb resta confrontabile fra tokenizer.
3. **Compute.** Stime su ~65 GFLOPS sostenuti: una run a 1/16 costa 0.5–1 h su CPU, una a 1/4
   6–17 h. Tutto E0 e il pilota E1 a 1/16 girano su CPU; la GPU a noleggio per 1/4 e 1×
   (~$5–20 per la griglia E1) si decide con un ADR solo se il pilota mostra un segnale.
4. Il punto 2 della Decision vale per il verdetto finale; il pilota a 1/16 dà un segnale, non un
   verdetto.
