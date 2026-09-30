# Experiments roadmap

Owner delle definizioni E0–E4. Non possiede i risultati ([`evidence/`](evidence/README.md)).
Stato di tutti gli E*: **specified** (2026-09-30). Tesi: [concept v0.2](concept.md).

Regole comuni ([ADR 0002](adr/0002-adversary-dense-frontier.md), [ADR 0003](adr/0003-lab-practices.md),
[ADR 0004](adr/0004-miniature-budgets.md)): budget 1/16, 1/4, 1× di 11 Mbit; in miniatura contano
solo i byte codificati del modello, con embedding ~15%; parità di token **e** di FLOP riportate;
gate appaiato > max(0.02 bpb, 2σ). Se F1 scatta, E2–E4 sono _won't run_.

## Sequenza

| #   | Passo                                        | Dove      | Costo stimato                    |
| --- | -------------------------------------------- | --------- | -------------------------------- |
| 1   | E0-lite: banco + frontiera scalare a 1/16    | CPU       | 1–2 giorni di codice, ore di run |
| 2   | Taratura: burst/sostenuto, σ su 3 seed       | CPU       | 30 min + 3 run                   |
| 3   | E1 pilota a 1/16, K=1                        | CPU       | 1–2 giorni di run                |
| 4   | Decisione: ADR GPU per 1/4 e 1×, oppure stop | —         | —                                |
| 5   | E1a ricorsione, E1 a 1/4, E1b trellis/segni  | GPU       | ~$5–20                           |
| 6   | E2 → E3 → E4                                 | GPU + CPU | —                                |

## E0-lite — Banco e frontiera scalare

- **Dati**: TinyStoriesV2-GPT4 `.txt` scaricato direttamente, deduplicato e ri-splittato
  (val ufficiale contaminato, [R5](research/05-eval-tiny.md)); test OOD separato.
- **Tokenizer**: a byte (V=256) a 1/16 e 1/4. BPE solo a 1×.
- **Modello**: transformer minuscolo, embedding tied a 4 bit; QAT ternario e 2-bit sul core.
- **Harness**: conteggio byte con rANS dei tensori, bpb dal log-prob sull'held-out. Senza flag → help.
- **Test prima del codice**: round-trip rANS, conteggio byte su tensori noti, bpb su distribuzione nota.
- **Output**: miglior forma e formato scalare a 1/16, forma congelata per E1.

**Problema aperto (1/4).** Con tokenizer a byte (V=256) l'embedding a 1/4 vale solo 1024·d bit:
il vincolo ~15% si soddisfa solo con modelli larghi e da 2–3 layer, una forma degenere. Prima di
E1 a 1/4 va deciso fra BPE 512 o un vincolo di quota rilassato; non tocca il pilota a 1/16.

## Taratura

- Fattore burst/sostenuto misurato dai tok/s dei run E0-lite a 4 thread fuori slice, che corregge tutte le stime di costo.
- 3 seed del punto migliore di E0-lite → σ → gate.

## E1 pilota — Core vettoriale contro scalare a 1/16 (segnale su F1, F1-abl)

- K=1, nessuna ricorsione. 3 seed, rate vettoriale 0.5 e 0.75 bit/peso, token ≈ 20 per parametro
  stoccato del braccio più grande, uguali per tutti.
- **Scalari**: ternario (codificato sugli zeri), 2-bit. **Vettoriali**: VQ-seed, VQ-appreso con
  codebook condiviso (byte contati).
- **Ricetta VQ**: assegnazione al codebook periodica (ogni N step, non a ogni step: costerebbe
  quanto il forward) con reseed dei codici morti, quantizzazione parziale stile Quant-Noise
  ([R7](research/07-learned-vq-subbit.md)).
- **Segnale F1**: il miglior vettoriale batte il miglior scalare di max(0.02, 2σ).
- **Segnale F1-abl**: VQ-appreso contro VQ-seed, codebook incluso (prior: seed ≥ appreso).
- Il pilota non è un verdetto ([ADR 0004](adr/0004-miniature-budgets.md)): decide se pagare la GPU.

## E1a — Diversità fra iterazioni (chiude v0.1, sceglie la ricorsione)

Budget 1/4, core del braccio vincente del pilota, stessi token e FLOP, 3 seed:

| Braccio            | Cosa aggiunge alla ricorsione pura b0                                    |
| ------------------ | ------------------------------------------------------------------------ |
| b0                 | niente, blocchi condivisi × K iterazioni                                 |
| + iter-emb         | un vettore per iterazione                                                |
| + IA³              | scaling diagonale per matrice per iterazione                             |
| + LoRA r=1         | rank-1 per matrice per iterazione                                        |
| + randn J∈{1,8,64} | matrici casuali fisse in RAM, coefficienti `c` appresi (v0.1 senza PRNG) |
| tetto              | K blocchi slegati, stesso compute                                        |

Se randn ≤ IA³/LoRA r=1 a pari bit, **v0.1 è killed**. Se tetto − b0 < gate, si usa b0.

## E1 a 1/4 e E1b

- E1 ripetuto a 1/4 per i 2–3 bracci migliori del pilota, con la ricorsione di E1a: il verdetto F1
  richiede lo stesso segno a 1/16 e 1/4.
- E1b: trellis calcolato stile QTIP (quantizzazione di Viterbi nel training) e ibrido segni
  low-rank (Sign Lock-In) + magnitudini VQ.
- Distillazione, se si usa, solo con teacher nostro sullo stesso tokenizer, per tutti i bracci.

## E2 — Codifica e rate loss per tutti (attacca F2)

- Rate loss `NLL + λ·bit(descrizione)` e rANS su tutti i bracci; sweep di λ con lo stesso budget
  di ricerca per braccio.
- **Gate**: il vantaggio del vettoriale sopravvive sui byte codificati.
- **Controllo MDL**: corpus compresso + trainer al boot (codice prequenziale), atteso fuori F3.

## E3 — Scala piena e costo di boot (attacca F3)

- Budget 1× a convergenza, BPE, immagine intera nel conto.
- Boot sul runtime C: decodifica indici, RSS di picco, tok/s mediani su 5 run;
  hash dei pesi espansi identico su 5 boot.

## E4 — Immagine reale (attacca F4)

_Won't run_ finché E1 ed E2 non passano.

- Binario statico musl + tokenizer + descrizione su immagine FAT12 da 1 474 560 B, montata ed eseguita.
- bpb dal runtime; coerenza con giudice LLM a versione fissata, 50 prompt × 4 campioni,
  TinyStories-8M nella stessa sessione, 30 campioni in revisione umana cieca
  ([R5](research/05-eval-tiny.md)).
