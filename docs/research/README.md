# Survey — contratto

Ogni file `0N-*.md` risponde a **una** domanda. Non è una bibliografia.
Stesso contratto delle survey di [SmallerGPT](../../../smallergpt/docs/research/README.md).

## Sezioni obbligatorie

1. **Domanda** — una, in una frase.
2. **Cosa esiste** — citazioni 2024–2026 (e precedenti load-bearing), lette almeno in abstract + claim centrale.
3. **Cosa manca** — il gap, con il contro-esempio cercato dichiarato.
4. **Implicazione per FloppyLM** — quale F* tocca.
5. **Esperimento minimo** — di solito un E* della [roadmap](../experiments-roadmap.md).

## Divieti

- Claim di "buco di letteratura" senza aver cercato un contro-esempio.
- Promuovere un paper a design. Il design sta in [`concept.md`](../concept.md).
- Survey senza data in testa.

## Indice

| Survey                                                     | Domanda                                                                                                       |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| [01-tiny-lms.md](01-tiny-lms.md)                           | Cosa sa fare il miglior LM denso ≤10M param, e quanti byte costa?                                             |
| [02-procedural-weights.md](02-procedural-weights.md)       | Esiste già un LM da zero con descrizione ≤1.44 MB che sfrutta riposo vs RAM? (decide F0)                      |
| [03-mdl-compression.md](03-mdl-compression.md)             | Quanto costa in bit un LM, e il training rate-aware sposta la frontiera?                                      |
| [04-runtime-and-demoscene.md](04-runtime-and-demoscene.md) | Quanti byte si mangia il runtime, cosa insegna la demoscene?                                                  |
| [05-eval-tiny.md](05-eval-tiny.md)                         | Come si confrontano modelli minuscoli a parità di byte senza trucchi?                                         |
| [06-hardware-budget.md](06-hardware-budget.md)             | Cosa si allena e cosa si espande in tempo utile su questo laptop?                                             |
| [07-learned-vq-subbit.md](07-learned-vq-subbit.md)         | Esiste un LM da zero con VQ a codebook appreso sotto 1 bit/peso? Appreso vs seed vs ternario (decide F0 v0.2) |
