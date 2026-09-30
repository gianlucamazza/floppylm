# Experiments roadmap

Owner delle definizioni E0–E4. Non possiede i risultati ([`evidence/`](evidence/README.md)).
Stato: E0 v2 **stub → codice pronto, campagna non avviata**; tutti gli altri E* **specified** (2026-09-30). Tesi: [concept v0.2](concept.md).

Regole comuni ([ADR 0002](adr/0002-adversary-dense-frontier.md), [ADR 0003](adr/0003-lab-practices.md),
[ADR 0004](adr/0004-miniature-budgets.md)): budget 1/16, 1/4, 1× di 11 Mbit; in miniatura contano
solo i byte codificati del modello, con embedding ~15%; parità di token **e** di FLOP riportate;
gate appaiato > max(0.02 bpb, 2σ). Se F1 scatta, E2–E4 sono _won't run_.

## Sequenza

| #   | Passo                                                                     | Dove      | Costo stimato     |
| --- | ------------------------------------------------------------------------- | --------- | ----------------- |
| 1   | E0 v2: codice e smoke (fatto), campagna a–e dopo l'approvazione di S1–S10 | CPU       | ore–giorni di run |
| 2   | σ appaiata e congelamento dell'avversario (passo e)                       | CPU       | 5 seed            |
| 3   | E1 pilota a 1/16, K=1                                                     | CPU       | 1–2 giorni di run |
| 4   | Decisione: ADR GPU per 1/4 e 1×, oppure stop                              | —         | —                 |
| 5   | E1a ricorsione, E1 a 1/4, E1b trellis/segni                               | GPU       | ~$5–20            |
| 6   | E2 → E3 → E4                                                              | GPU + CPU | —                 |

## E0 v2 — Scelte da approvare

Le decisioni approvate stanno in [ADR 0005](adr/0005-e0v2-protocol.md). Queste sono le **scelte
numeriche nuove**, implementate come default nel codice ma **non ancora approvate**; nessuna campagna
parte finché non lo sono.

| #   | Scelta                         | Default proposto                                                                                                                                                                                  |
| --- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| S1  | Base di token T                | 20 × parametri stoccati; cooldown che terminano a T, 2T, 4T                                                                                                                                       |
| S2  | Forma del WSD                  | warmup lineare sul 2% di T; cooldown lineare a zero sul 10% dei token di ogni ramo                                                                                                                |
| S3  | Aggiustamento fuori tolleranza | un solo nuovo tentativo per forma e braccio: solver ri-eseguito con target / (coded/nominal misurato); se ancora fuori, run escluso                                                               |
| S4  | Budget di tuning               | 6 run per braccio: lr ∈ {1e-3, 3e-3, 1e-2} × secondo asse (ternario: Δ ∈ {0.5, 0.7} con wd 0.1; 2-bit: wd ∈ {0, 0.1})                                                                             |
| S5  | Seed                           | 3 seed minimi per confronto; 5 se la differenza media appaiata è sotto 2 × gate                                                                                                                   |
| S6  | FLOP stimati                   | forward per token = 2 × parametri stoccati + 4 × n_layers × (ctx/2) × d; training = 3 × forward × token; valutazioni escluse e riportate a parte in wall clock                                    |
| S7  | Valutazione                    | finestra scorrevole, stride ctx/2, ogni byte bersaglio contato una volta, ultima finestra allineata alla fine; il separatore 0x03 è un bersaglio normale; val sul primo MiB, test sui primi 2 MiB |
| S8  | Politica delle scale           | scelta dall'A/B del passo b fra `row16`, `row8log`, `tensor16`                                                                                                                                    |
| S9  | Righe nulle                    | scala 0 esatta, ricostruzione esattamente nulla in tutti i formati; `row8log` riserva il codice 0 alla scala nulla                                                                                |
| S10 | Dati                           | deduplicazione esatta (sha1 del testo) è l'unica capacità attuale; filtro near-duplicate e test OOD restano requisiti successivi                                                                  |

## E0 v2 — Banco e frontiera scalare

Protocollo in [ADR 0005](adr/0005-e0v2-protocol.md); harness `experiments/e0_v2.py`. La griglia
E0-lite pre-v2 è diagnostica ([pre-v2](evidence/e0-lite/pre-v2/notes.md)).

- **Dati**: TinyStoriesV2-GPT4, deduplicazione esatta, split per hash; preparazione riprodotta
  dai raw il 2026-09-30 (`data/tinystories/reproducibility.json`). Near-duplicate e OOD: dopo (S10).
- **Tokenizer**: a byte (V=256) a 1/16 e 1/4. BPE solo a 1×.
- **Modello**: core ternario o 2-bit con politica di scala unica, embedding tied 4 bit, norme fp16,
  MLP GELU / ReLU² / SwiGLU, QK-norm opzionale.
- **Forma**: il solver (`floppylm.shapes`) propone forme a 99.5–100% dei bit nominali; ammissibilità
  sui byte serializzati (`--parity`).
- **Training**: WSD con tronco e cooldown a T/2T/4T, checkpoint del tronco, saturazione a 4T.
- **Selezione e test**: `--freeze` congela gli hash; `--final-test` legge il test una sola volta.

Campagna (non avviata; richiede S1–S10 approvate):

a. Velocità: 4 run × 1 thread contro 1 run × 4 thread; `torch.compile` solo se funziona e accelera.
b. A/B neutri a pari byte, ternario, 2 seed: politica delle scale; GELU vs SwiGLU vs ReLU².
c. Tuning con budget S4 per ternario e 2-bit.
d. Griglia del solver con WSD: curva di saturazione e parità per forma.
e. σ appaiata su 5 seed al punto migliore → gate; congelamento dell'avversario; `notes.md` e `summary.json`.

**Problema aperto (1/4).** Con tokenizer a byte (V=256) l'embedding a 1/4 vale solo 1024·d bit:
il vincolo ~15% si soddisfa solo con modelli larghi e da 2–3 layer, una forma degenere. Prima di
E1 a 1/4 va deciso fra BPE 512 o un vincolo di quota rilassato; non tocca il pilota a 1/16.

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
