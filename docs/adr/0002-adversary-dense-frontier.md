# ADR 0002: Avversari fissati prima della tesi

## Status

Accepted — 2026-09-30. Amended — 2026-09-30 (due volte).

## Context

SmallerGPT ha perso due linee contro un CharGRU banale
([verdetto](../../../smallergpt/docs/verdict.md)). Qui la survey ha già trovato un avversario più
forte della tesi originale: a ~5 MB la ricorsione pura batte i pesi da seed + LoRA di 0.15 bpb
([R2](../research/02-procedural-weights.md)). Parameter Golf mostra anche che int6 QAT + GPTQ +
Brotli è la baseline affidabile e che la forma del modello sposta il verdetto
([R1](../research/01-tiny-lms.md), [R3](../research/03-mdl-compression.md)).

## Decision

1. Due avversari, non uno: **frontiera densa basso-bit** (miglior punto di E0 a 1.44 MB, dopo
   ricerca di forma) e **ricorsione pura** (blocchi condivisi, senza seed).
2. Stesso trattamento per tutti i bracci: token di training, budget di ricerca iperparametri e forma,
   pruning, entropy coding, rate loss.
3. La frontiera densa si congela prima di aprire E1. Non si rilancia dopo aver visto E1.

## Consequences

- La tesi vince solo se batte la ricorsione pura: i seed devono pagare i propri bit.
- Una vittoria contro il solo denso non è un risultato della tesi.

## Amendment — 2026-09-30 (stress test v0.1)

Lo stress test della tesi v0.1 ([concept § Stress test](../concept.md)) ha mostrato che su CPU un
confronto a soli token uguali è compute-limited e premia il braccio più economico per token.

1. **Distillazione per tutti**: ogni braccio si addestra con la stessa loss di distillazione da
   un teacher fissato (TinyStories-33M, logit precalcolati su disco), oltre alla NLL.
2. **Doppia parità**: ogni confronto riporta sia parità di token sia parità di FLOP di training.
3. **Avversario riaddestrato** al budget di token/FLOP dell'esperimento che lo usa; il punto 3
   della Decision vale per forma e iperparametri, non per il numero di token.
4. **Gate appaiato**: differenza media fra bracci sugli stessi seed > max(0.02 bpb, 2σ), con σ
   misurata in E0 su 3 seed.
5. Il terzo avversario è la **ricorsione ternaria** (ricorsione pura con core a 1.58 bit).

## Amendment 2 — 2026-09-30 (valutazione dei prossimi step)

Il punto 1 dell'amendment precedente è **sospeso**. Distillare da TinyStories-33M non è fattibile
così: tokenizer diversi (GPT-Neo 50k contro 256–1024) rendono i logit non confrontabili senza
allineamento, e logit completi su ~10⁸ token richiedono terabyte. TinyStories è già testo generato
da un teacher più forte.

- La distillazione esce dal percorso critico. Rientra solo come trattamento uniforme per tutti i
  bracci, con un teacher **nostro** sullo stesso tokenizer e top-16 logit su disco.
- Il punto 5 (ricorsione ternaria) vale dal budget 1/4; il pilota E1 a 1/16 è senza ricorsione.
