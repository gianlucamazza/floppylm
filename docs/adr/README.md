# ADR — decisioni strutturali

Un ADR esiste solo per una decisione **già presa** e costosa da ribaltare.
Non è un brainstorm, non è una survey, non è un TODO. Stesse regole di
[SmallerGPT](../../../smallergpt/docs/adr/README.md).

## Regole

1. Status: `accepted` | `amended` | `superseded`. Niente `proposed`: le proposte vivono in `concept.md`.
2. Un ADR non si riscrive in silenzio: si amenda con data o si supersede.
3. Il design normativo applica gli ADR, non li duplica.

## Indice

| ADR                                      | Decisione                                                                                                    |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| [0001](0001-floppy-budget.md)            | Budget = 1 474 560 byte per l'immagine intera; cosa conta e cosa no                                          |
| [0002](0002-adversary-dense-frontier.md) | Avversari fissati prima: frontiera densa, ricorsione ternaria; distillazione e doppia parità per tutti       |
| [0003](0003-lab-practices.md)            | Invarianti di laboratorio: bit-accounting, seed, evidence, stop su F\*                                       |
| [0004](0004-miniature-budgets.md)        | Budget 1/16, 1/4, 1×: solo byte del modello, embedding ~15%, CPU per il pilota, GPU con ADR                  |
| [0005](0005-e0v2-protocol.md)            | Protocollo E0 v2: parità sui byte serializzati, WSD, saturazione, compute, selezione protetta, tracciabilità |
| [0006](0006-flp2-only.md)                | FLP2 unico formato; FLP1 rifiutato, leggibile solo alla revisione `f9e0732`                                  |
| [0007](0007-e0v2-review-gates.md)        | Review gates: scientific/functional freeze, exact grid arguments, inference-only artifacts, tracked evidence |
