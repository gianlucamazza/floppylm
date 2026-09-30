# Concept — FloppyLM v0.2

Owner della tesi, dei principi e di F0–F4. Status: **specified** (2026-09-30). v0.1 è un record
in [§ Stress test v0.1](#stress-test-v01). Numeri di letteratura nelle survey; numeri propri in
[`evidence/`](evidence/README.md).

## Vincolo

Un language model la cui immagine intera — descrizione dei pesi, tokenizer, runtime — sta su un
floppy 3.5" HD reale: **1 457 664 B di area dati FAT12** ([ADR 0001](adr/0001-floppy-budget.md)).
Tolti runtime e tokenizer restano ~1.38–1.42 MB ≈ **11 Mbit** per il modello
([R4](research/04-runtime-and-demoscene.md)).

## Osservazione di partenza

Il floppy limita i **bit a riposo**, non la RAM a runtime (1 GB,
[R6](research/06-hardware-budget.md)). Un denso ternario codificato sugli zeri costa ~1.485
bit/peso: tetto ~7M param ([R1](research/01-tiny-lms.md)). Oltre si entra nel **regime sotto il
bit**, e lì la domanda è una sola: **dove stanno i bit**. A 11 Mbit il core del transformer ne
porta ~2/3–3/4, l'embedding il resto; qualunque meccanismo che agisca altrove è decorazione
(lezione dello stress test sotto, e di [smallergpt](../../smallergpt/docs/verdict.md)).

## Cosa non è nuovo (F0 parziale)

- Pesi da seed + adapter su LM sotto vincolo di byte: Parameter Golf, dove la ricorsione pura vince
  ([R2](research/02-procedural-weights.md)).
- LM da zero con product quantization a ~1.3 bit/peso, ~0.65 per peso effettivo con condivisione
  di layer: Quant-Noise ([R7](research/07-learned-vq-subbit.md)).
- LM a caratteri da zero a ~0.5–0.7 bit/peso con template di segni low-rank: Sign Lock-In (R7).
- Codebook appresi a 0.7–1.0 bit, solo post-training su LLM grandi: BTC-LLM, GLVQ (R7).

Nessun lavoro trovato addestra da zero un LM con **core codificato a vettori sotto 1 bit/peso**
e confronta **codebook appreso, da seed e calcolato** a parità esatta di byte codificati, sotto
1.5 MB, con artefatto avviabile. La novità rivendicabile è quel confronto e il suo risultato, non
il meccanismo.

## Tesi

**Sotto il bit, un core ricorsivo i cui pesi sono indici in un codice vettoriale batte a parità
di byte codificati il miglior core scalare (ternario, 2-bit) con la stessa ricorsione.**

Il core si scrive `W = D(indici)`, blocchi di `v` pesi → un indice da `r·v` bit (0.5–0.75 bit/peso),
con tre decodificatori `D` in gara:

| Braccio               | Codice                                        | Byte del codice                           | Prior da letteratura (R7)                    |
| --------------------- | --------------------------------------------- | ----------------------------------------- | -------------------------------------------- |
| **VQ-seed**           | codebook generato da PRNG, fissato            | 0                                         | favorito: QTIP, FSQ, "solo i ranghi contano" |
| **Trellis calcolato** | codice calcolato stile QTIP, rate frazionario | 0                                         | favorito, batte VQ-8 a pari rate su LLM      |
| **VQ-appreso**        | codebook appreso, condiviso fra layer         | K·v·b_c (~0.8 Mbit a K=4096, v=24, 8 bit) | sfavorito: paga i propri byte                |

Il trellis richiede una quantizzazione di Viterbi dentro il loop di training: entra in E1b, dopo
il pilota con VQ-seed e VQ-appreso ([roadmap](experiments-roadmap.md)).

La scommessa non è "appreso batte casuale": è che **addestrando da zero, i pesi si adattano al
codice** e il regime sotto il bit diventa accessibile senza il muro del segno (Sign Lock-In, R7).
Il confronto appreso vs calcolato è pre-registrato con prior contrario all'appreso: se l'appreso
vince, deve farlo includendo i byte del codebook.

Conto indicativo a 11 Mbit (d=384, V=1024 tied):

| Componente                 | Param                      | bit/param | Mbit                    |
| -------------------------- | -------------------------- | --------- | ----------------------- |
| Embedding                  | 0.39M                      | 4         | 1.6                     |
| Core, VQ a 0.5 bit/peso    | ~18.6M unici (~10 blocchi) | 0.5       | 9.3                     |
| Codebook (solo VQ-appreso) | —                          | —         | 0.8 (sottratto al core) |
| Norme, scale               | —                          | —         | 0.1                     |

Contro il ternario (~6M param di core, ~3.5 blocchi) il core sotto il bit ha ~3× i pesi unici;
la ricorsione li moltiplica ancora. L'embedding a 4 bit è ora ~15%: vocab 512–2048 si sceglie in E0.

## Principi

- **P1 — Contare tutto.** Il numero è `image_bytes` sul file reale ([ADR 0003](adr/0003-lab-practices.md)).
- **P2 — Avversari forti, trattati uguale.** Denso ternario/2-bit e ricorsione ternaria, stesso
  entropy coding, stessa rate loss; doppia parità token/FLOP
  ([ADR 0002](adr/0002-adversary-dense-frontier.md)).
- **P3 — Byte codificati, non bit nominali.** Gli indici VQ sono vicini a entropia massima, il
  ternario sparso guadagna dall'entropy coding: si confronta dopo la codifica (R7, F2).
- **P4 — Convergenza prima del verdetto.** F1 si decide ai budget in miniatura dove tutti i bracci
  saturano ([ADR 0004](adr/0004-miniature-budgets.md)).
- **P5 — Qualità per byte, non "gira su floppy".** bpb held-out dal runtime C; coerenza TinyStories
  secondaria ([R5](research/05-eval-tiny.md)).

## Falsificazione

Gate = differenza media appaiata sugli stessi seed > max(0.02 bpb, 2σ), σ misurata in E0.

| F      | Scatta se                                                                                                                                   | Attaccato da                                                                                                  |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| F0     | Un lavoro fa già il confronto appreso/seed/calcolato sotto 1 bit, da zero, ≤ 1.5 MB                                                         | continuo; oggi **parziale** ([R2](research/02-procedural-weights.md), [R7](research/07-learned-vq-subbit.md)) |
| F1     | Nessun braccio vettoriale batte il migliore fra ternario e 2-bit (stessa ricorsione) sui byte codificati, a entrambi i budget in miniatura  | E1                                                                                                            |
| F1-abl | VQ-appreso non batte il migliore fra VQ-seed e trellis: il learning del codice non conta (atteso; decide il meccanismo, non uccide la tesi) | E1                                                                                                            |
| F2     | Il vantaggio sparisce quando tutti i bracci ricevono entropy coding + rate loss                                                             | E2                                                                                                            |
| F3     | Espansione > 60 s, RSS > 1 GB, o < 5 tok/s sul binario C                                                                                    | E3                                                                                                            |
| F4     | Coerenza non non-inferiore a TinyStories-8M (margine 0.5) o sotto grammatica 6 / consistenza 5                                              | E4                                                                                                            |

## Limiti dichiarati

- Dominio TinyStories: nessuna conoscenza fattuale attesa.
- Training a scala piena su GPU a noleggio solo con ADR dedicato ([ADR 0004](adr/0004-miniature-budgets.md)).
- Eval fissata prima dei numeri: niente cache n-gram o TTT in valutazione ([R2](research/02-procedural-weights.md)).
- VQ-QAT puro straight-through è fragile (Quant-Noise: peggio del post-training); la ricetta è
  quantizzazione parziale / snapping periodico con reseed dei codici morti (R7).

## Stress test v0.1

Record della tesi v0.1 (2026-09-30), chiusa prima di essere implementata.

**Tesi v0.1.** Core ricorsivo condiviso perturbato per iterazione:
`W[b,k] = W_core[b] + Σ_j c[b,k,j]·G(seed[b,k,j])`, coefficienti `c` sotto loss MDL.

**Perché è stata chiusa** (valutazione propria + reviewer indipendente a freddo, convergenti):

1. **Dove stanno i bit.** A V=2048, d=384: embedding ~28%, core ~64%, coefficienti `c`
   **0.03–0.2%**. La tesi innovava sulla componente che non porta il segnale.
2. **Il seed non porta informazione.** J direzioni casuali in D≈d² catturano una frazione J/D
   dell'energia di un delta utile; cercare il seed a 16 bit dà coseno massimo ≈ √(2 ln 2¹⁶ / D)
   ≈ 0.012. I parametri "in più" hanno zero bit: la rate loss spinge `c` → 0.
3. **Prior contro.** A ~5 MB la ricorsione pura batte seed + LoRA di 0.15 bpb (R2); a pari bit
   iteration embedding, IA³ e LoRA rank-1 hanno direzioni allineate e dominano quelle isotrope.
4. **Metodologia.** Su CPU E1 era compute-limited; gate senza σ; distillazione assente. Corretti in
   [ADR 0002](adr/0002-adversary-dense-frontier.md) (amendment) e [ADR 0004](adr/0004-miniature-budgets.md).

Il test che la chiude formalmente è **E1a** in [roadmap](experiments-roadmap.md), dopo il pilota
E1: serve comunque a scegliere la ricorsione per il budget 1/4. Lo spirito procedurale sopravvive spostato dove stanno i bit: il
codebook da seed è ora un braccio favorito del core.
