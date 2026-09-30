# ADR 0005: Protocollo E0 v2

## Status

Accepted — 2026-09-30. §10 superseded in parte da [ADR 0006](0006-flp2-only.md) (niente FLP1).
Supersede ADR 0003 §2 e §7 (parità, selezione) e la regola "20 token per
parametro" di ADR 0004 §1. Gli ADR 0003 e 0004 restano validi per tutto il resto.

## Context

La griglia E0-lite (pre-v2) non poteva decidere F1: forme con riempimento del budget fra 0.88 e 0.99,
nessuna curva di saturazione, avversario non tarato, test valutato dentro il run di training. Due
revisioni indipendenti hanno converso sulle correzioni ([roadmap](../experiments-roadmap.md)).
Questo ADR registra **solo le decisioni approvate** dall'utente il 2026-09-30. Le scelte numeriche
nuove, non ancora approvate, stanno in
[roadmap § Scelte da approvare](../experiments-roadmap.md#e0-v2--scelte-da-approvare).

## Decision

1. **Parità dei byte.** I bit nominali servono solo al solver per proporre forme. L'ammissibilità si
   decide sui byte realmente serializzati (`len(pack(model))`): ogni candidato entro ±1% del target
   **e** `max(bytes)/min(bytes) − 1 ≤ 0.01` fra i candidati confrontati. Nessun padding. Un run fuori
   tolleranza si conserva come diagnostica e si esclude dai verdetti.
2. **Aggiustamento dopo entropy coding.** Se un braccio esce di tolleranza, la forma si riaggiusta con
   una regola dichiarata prima della campagna e con lo stesso numero di tentativi per braccio.
3. **WSD.** Un tronco a LR costante con warmup; cooldown lineari a zero che terminano a T, 2T, 4T,
   ognuno ramificato da una copia del tronco. Il tronco non è mai modificato dai cooldown. Il
   checkpoint del tronco contiene modello, optimizer, stato dello scheduler, RNG e posizione nel
   flusso dati; la ripresa da checkpoint è deterministica.
4. **Saturazione.** Criterio `|bpb(4T) − bpb(2T)| < 0.01` sul val, registrando anche il delta con
   segno. Se a 4T fallisce, il run è dichiarato **non saturo**; nessun prolungamento automatico.
5. **Compute.** Token e FLOP stimati si registrano separati per tronco, per ogni cooldown e in totale
   (costo della ricerca), insieme alla formula, agli arrotondamenti e alle risorse consumate (wall
   clock, thread). I confronti dichiarano se sono a token uguali o a compute stimato uguale.
6. **Budget di tuning.** Numero di run fissato per braccio, uguale per tutti i bracci confrontati.
7. **σ appaiata.** La σ del gate è la deviazione standard delle differenze fra due condizioni nominate
   sugli stessi seed. La dispersione di un solo modello non è una σ appaiata.
8. **Selezione protetta.** Training e tuning leggono solo train e val. Il test si valuta con un
   comando separato, dopo aver salvato una selezione congelata legata agli hash degli artefatti.
9. **Tracciabilità.** Ogni run ha id univoco, directory creata in esclusiva, scritture atomiche, stato
   `running | completed | failed | interrupted`, manifest con hash di dati, sorgenti, configurazione,
   ambiente e artefatto. Un run incompleto non appare mai completato.
10. **Formato.** `pack(unpack(blob)) == blob` per ogni formato supportato, incluso il legacy `FLP1`;
    simboli e scale caricati sono canonici e non si riquantizzano al risalvataggio.

## Consequences

- I risultati pre-v2 restano come diagnostica in [`evidence/e0-lite/pre-v2`](../evidence/e0-lite/pre-v2/notes.md).
- Nessuna campagna E0 v2 parte prima che le scelte da approvare siano approvate.
