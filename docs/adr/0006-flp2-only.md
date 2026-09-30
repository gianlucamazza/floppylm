# ADR 0006: FLP2 è l'unico formato supportato

## Status

Accepted — 2026-09-30. Supersede la parte "incluso il legacy `FLP1`" di
[ADR 0005](0005-e0v2-protocol.md) §10. Il resto di ADR 0005 resta valido.

## Context

ADR 0005 §10 chiedeva di leggere e risalvare anche gli artefatti `FLP1` della griglia E0-lite
pre-v2. L'utente ha poi chiesto di evitare codice e architettura legacy non necessari. Nessun
percorso E0 v2 dipende da `FLP1`: gli artefatti pre-v2 sono diagnostica esclusa dai verdetti
([pre-v2](../evidence/e0-lite/pre-v2/notes.md)), e il loro formato richiedeva un decoder rANS a
12 bit, regole di scala proprie e una variante dell'architettura.

## Decision

1. Il codice attivo supporta solo `FLP2`, con round-trip byte-identico (`pack(unpack(b)) == b`).
2. Un blob `FLP1` è rifiutato con `FormatError` esplicito che indica la revisione di riferimento.
3. La revisione Git **`f9e0732`** è il riferimento per leggere gli artefatti storici. Lì è
   verificato che i tre blob `FLP1` si risalvano identici e che `experiments/verify_pre_v2.py`
   riproduce esattamente il val bpb registrato (d64L6 2.0129680935772494, d80L4
   1.8551768137161695).
4. Gli artefatti pre-v2 restano su disco (fuori da Git) e sono documentati con i loro hash.

## Consequences

- Rimossi dal codice attivo: decoder rANS a 12 bit, regola di quantizzazione `flp1`, campo
  `rule` della configurazione, ramo `FLP1` di `pack`/`unpack`, lo script di verifica e il
  vecchio harness `e0_lite.py`.
- `tests/fixtures/flp1_smoke.flp` resta nel repo solo per il test di rifiuto.
