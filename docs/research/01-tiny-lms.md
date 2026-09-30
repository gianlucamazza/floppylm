# Survey 1 — Il miglior LM denso sotto i 10M parametri e il suo costo in byte

Consolidato da ricerca web del 2026-09-30.

## Domanda

Cosa sa fare oggi il miglior LM denso da ≤10M parametri, e quanti byte costa, cioè qual è la frontiera
densa che un floppy da 1 474 560 byte può ospitare per intero (pesi + tokenizer + runtime)?

## Cosa esiste

**TinyStories** (Eldan & Li 2023, [arXiv:2305.07759](https://arxiv.org/abs/2305.07759)) è il punto di
partenza obbligato: un corpus sintetico di storie con il lessico di un bambino di 3–4 anni (circa 1500
parole base) generato da GPT-3.5/GPT-4, su cui modelli GPT-Neo da ~1M a ~33M parametri producono storie
di più paragrafi "fluenti, coerenti e con grammatica quasi perfetta". Il tokenizer è quello di GPT-Neo
ridotto ai 10K token più frequenti, contesto 512. La tesi centrale, verificata leggendo il paper, è che la
grammatica emerge presto mentre coerenza e creatività richiedono più capacità: la coerenza con l'inizio
della storia compare quando la dimensione nascosta passa da 64 a 128, la profondità conta più per il
tracking del contesto e l'ampiezza più per i fatti. Sul singolo esempio "Lucy e la scala" GPT-4 assegna
(grammatica/creatività/coerenza, su 10): 1M a 8 layer 6/3/2, 2.5M a 8 layer 5/6/3, 8.3M a 8 layer 7/5/5,
28M a 8 layer 9/6/9, 21M a 1 layer 8/–/7. Il modello da 1M non risponde correttamente a nessun prompt
fattuale e produce spesso frasi agrammaticali; il 28M batte GPT2-XL (1.5B) su questi prompt. Questi
numeri sono per-esempio, non medie: vanno letti come ordini di grandezza. Un dettaglio decisivo per noi:
i conteggi "1M/3M/8M" dei checkpoint HF non sono byte-realistici. `TinyStories-1M` ha hidden 64, 8 layer
e `vocab_size` 50257 nel config, quindi la sola matrice di embedding vale ~3.2M parametri; il repository
pesa 51.9 MB e il solo `tokenizer.json` pesa 2.11 MB, più dell'intero floppy.

**llama2.c** (Karpathy, [github.com/karpathy/llama2.c](https://github.com/karpathy/llama2.c)) è la
reference più vicina al nostro artefatto perché separa in modo pulito checkpoint, tokenizer e runtime:
`run.c` è ~700 righe di C puro in float32, `runq.c` aggiunge int8 Q8_0 (checkpoint 4× più piccoli, ~3×
più veloce). I modelli TinyStories pubblicati sono 260K (dim 64, 5 layer, 8 teste, 4 kv, ctx 512,
val loss 1.297), 15M (dim 288, 6 layer, val loss 1.072), 42M (0.847) e 110M (0.760). Il 260K
([doc/stories260K.md](https://github.com/karpathy/llama2.c/blob/master/doc/stories260K.md)) usa un
tokenizer custom da 512 token (`tok512.bin` 6.23 KB) e pesa 1.06 MB in fp32: in int8 sarebbe ~260 KB,
già oggi dentro il floppy con ampio margine; produce storie grammaticali ma ripetitive a temperatura 0.
Il 15M pesa ~60 MB fp32, ~15 MB int8, ~7.5 MB a 4 bit: fuori budget di un fattore ~5. Karpathy nota
inoltre che un tokenizer da 4096 token addestrato su TinyStories dà sequenze lunghe quanto quelle del
tokenizer Llama 2 da 32K: a scala minuscola il vocabolario grande è quasi solo costo.

**SimpleStories** (2025, [arXiv:2504.09184](https://arxiv.org/abs/2504.09184)) è il
successore diretto più rilevante: 2M storie parametrizzate in inglese e giapponese e una suite di modelli
da 1.25M (4 layer, d 128), 5M (6, 256), 11M (6, 384), 30M e 35M, tutti con un tokenizer WordPiece
morfologico da 4096 token. Gli autori dichiarano di "spostare la frontiera del modello con meno parametri
che produce linguaggio naturale grammaticale" e riportano che i loro modelli battono TinyStories-33M su
tutte le metriche di un giudice GPT-4o-mini (N=200), pur ammettendo che il vero limite inferiore resta
aperto. Nota di accounting: con V=4096 e d=128 l'embedding del modello 1.25M vale ~0.52M parametri, cioè
quasi metà del modello.

**Super Tiny Language Models** (Hillier, Guertler et al. 2024,
[arXiv:2405.14159](https://arxiv.org/abs/2405.14159)) è un programma di ricerca più che un risultato:
tokenizzazione byte-level con pooling, weight tying e training efficiente per tagliare i parametri del
90–95% puntando a 10M/50M/100M. Conferma la direzione (il vocabolario è il primo nemico) ma non fornisce
un punto di frontiera misurato a 10M.

**MobileLLM** (Liu et al., ICML 2024, [arXiv:2402.14905](https://arxiv.org/abs/2402.14905)) stabilisce a
scala sub-miliardo tre regole che valgono a maggior ragione per noi: meglio profondo e sottile che largo e
basso; condividere embedding di input e output (nel 125M risparmia ~16M parametri, l'11.8%, con −0.2
punti di accuratezza recuperabili spendendo i parametri in profondità); grouped-query attention. La
variante MobileLLM-LS ripete ogni blocco due volte (weight sharing a blocchi) e guadagna altri 0.7 punti
con +2.6% di latenza: è già una forma elementare di "descrizione procedurale espansa a runtime", e va
trattata come tale (vedi Implicazione).

**SmolLM2-135M** (Allal et al. 2025, [arXiv:2502.02737](https://arxiv.org/abs/2502.02737)) è il
riferimento superiore: 30 layer, hidden 576, vocabolario 49 152 con embedding legati (~28M parametri di
sola embedding, ~21% del totale), addestrato su ~2T token. In bf16 pesa ~270 MB, in 4 bit comunque
~70–100 MB: due ordini di grandezza sopra il floppy. Serve solo come ancora "cosa si ottiene quando il
budget non è il vincolo".

**Ternario.** BitNet b1.58 (Ma et al. 2024, [arXiv:2402.17764](https://arxiv.org/abs/2402.17764))
mostra pesi in {−1,0,+1} a 1.58 bit che eguagliano LLaMA fp16 a pari parametri e token, ma la tabella
dice che la parità arriva solo a 3B (700M: ppl 12.87 contro 12.33). Spectra/TriLM (Kaushal et al. 2024,
[arXiv:2407.12327](https://arxiv.org/abs/2407.12327)) conferma che il ternario vince a pari bit solo
sopra ~1B, con la suite che parte da 99M. Nielsen et al. ([arXiv:2411.05882](https://arxiv.org/abs/2411.05882))
trovano invece parità o meglio già su MLP, GNN e piccoli transformer, con un possibile effetto
regolarizzante. A scala microcontrollore, Atome LM ([github.com/TilelliLab/atome-lm](https://github.com/TilelliLab/atome-lm), 2026) impacchetta un 944K ternario byte-level (V=256) in un blob da 271 KB più un motore C99 da 2.6 KB,
ma documenta onestamente che a 944K il baseline fp32 vince di ~11% e che il modello è "a volte
incoerente". Il lavoro più recente, "Baseline Shape Decides the Verdict" (settembre 2026,
[arXiv:2609.29397](https://arxiv.org/abs/2609.29397)), rianalizza il presunto vantaggio del 22% dei blocchi
ternari instradati a 60K parametri e mostra che, a budget di byte fisso, la sola forma (profondità/larghezza)
di transformer a pari parametri sposta la loss del 22.6%: il vantaggio sparisce contro un baseline ben
dimensionato. Sul lato storage, BITCOS ([arXiv:2609.16338](https://arxiv.org/abs/2609.16338)) sfrutta la
densità di zeri (fino al 51.5%) per scendere a 1.485 bit/peso, sotto il limite 1.585 del packing ternario.

**Precisione e "più grande ma più piccolo".** Kumar et al., "Scaling Laws for Precision"
([arXiv:2411.04330](https://arxiv.org/abs/2411.04330)), modellano la bassa precisione come riduzione dei
"parametri effettivi" e osservano che il degrado da quantizzazione post-training cresce con i dati di
training: il modello denso deve essere addestrato quantization-aware, non quantizzato dopo. VBQ
([arXiv:2607.02893](https://arxiv.org/abs/2607.02893), 2026) apprende la precisione per gruppi da 64 pesi
in {1,2,4,8} bit (il 69% collassa a 1 bit) e su TinyStories un 131M a 1.82 bit medi raggiunge la
perplessità di un 55M fp16 con 3.8× meno storage. SeedLM (Apple 2024,
[arXiv:2410.10714](https://arxiv.org/abs/2410.10714)) codifica blocchi di pesi come seed di un LFSR più
pochi coefficienti, a 3–4 bit, su Llama 3 70B. Sono i due lavori più vicini alla tesi FloppyLM e vanno
citati come prior art per F0.

**BabyLM strict-small** ([findings 2025](https://aclanthology.org/2025.babylm-main.28/),
[arXiv:2504.08165](https://arxiv.org/abs/2504.08165)) vincola i _dati_ (10M parole), non i parametri:
i vincitori (GPT-BERT) sono modelli da decine di milioni di parametri. È rilevante per la pipeline di
valutazione (Survey 5), non per la frontiera in byte. Regional TinyStories
([arXiv:2504.07989](https://arxiv.org/abs/2504.07989)) conferma a 5–10M che tokenizer specifici per
lingua battono quelli generici.

**Il tokenizer come costo.** A questa scala l'embedding domina. Con d=192 la matrice legata costa
49K parametri a V=256 (byte-level), 98K a V=512, 393K a V=2048, 786K a V=4096, 1.9M a V=10K (TinyStories)
e 9.6M a V=50 257 (GPT-Neo): con un budget di ~2.8M parametri a 4 bit, V=4096 consuma già il 28% del
modello e V≥10K è semplicemente impossibile. Il file del tokenizer aggiunge ~6 KB a V=512 e qualche
decina di KB a V=4096; byte-level costa zero ma allunga le sequenze (≈1 byte/token contro ≈2–4) e quindi
il costo di inferenza e il contesto effettivo. Il compromesso ragionevole è BPE/unigram da 512–2048 token
addestrato sul corpus, con embedding legati.

**La frontiera a 1.44 MB, in conti.** Un floppy formattato FAT12 ha 1 474 560 byte grezzi ma, tolti boot
sector, due FAT da 9 settori e root directory da 14, restano 1 457 664 byte allocabili. Riservando
10–40 KB al runtime C statico (ordine di grandezza di `run.c` compilato con `-Os`) e ≤10 KB al tokenizer,
restano ~1.40 MB ≈ 11.2 Mbit per i pesi. Questo dà: ~1.4M parametri in int8; ~2.5M a 4 bit con scale
fp16 per gruppi da 32 (4.5 bit/peso) o ~2.8M con scale per riga; ~7.0M ternari impacchettati a 5 trit/byte
(1.6 bit/peso) e ~7.5M con codifica che sfrutta gli zeri. Una configurazione densa plausibile a 4 bit è
d=192, 5 layer, V=2048 legato (~2.6M parametri); in ternario d=320, 5 layer (~6.4M, embedding a 4 bit).
Per qualità, il 4 bit cade tra TinyStories 2.5M e 8.3M e vicino a SimpleStories 1.25M–5M: grammatica
buona (≈6–7/10), coerenza debole-media (≈3–5/10), nessuna conoscenza fattuale affidabile. In bpb, dalle
val loss di llama2.c (1.072 nat/token per il 15M con ~4 byte/token stimati ⇒ ~0.38 bpb; 1.297 per il 260K
con ~2.2 byte/token stimati ⇒ ~0.85 bpb) la frontiera da ~2.6M dovrebbe cadere intorno a 0.5–0.65 bpb
sul validation TinyStories; il rapporto byte/token è una nostra stima non pubblicata e va misurato in E0.

## Cosa manca

Non esiste in letteratura un modello denso pubblicato con accounting completo "pesi + tokenizer + runtime"
sotto 1.44 MB e qualità TinyStories dichiarata e misurata in bpb: i paper riportano parametri (spesso
senza embedding, alla Kaplan) o loss per-token con tokenizer diversi, mai byte su disco. Abbiamo cercato
esplicitamente controesempi alla tesi: (1) un LM denso ≤1.44 MB che già produca storie coerenti a livello
TinyStories-28M, e non l'abbiamo trovato (Atome 944K/271 KB è il più vicino ma si dichiara a volte
incoerente e sotto-addestrato, 3000 step); (2) prove che un modello più grande a meno bit batta un denso
più piccolo a pari byte sotto i 10M, e abbiamo trovato solo evidenze sopra i 50M (VBQ, Spectra, BitNet) più
un'evidenza contraria a 60K–944K (Baseline Shape, Atome); (3) descrizioni procedurali/seed-based dei pesi
(SeedLM, weight sharing di MobileLLM-LS) applicate a modelli sub-10M: nessuna. Mancano anche numeri bpb
pubblici e confrontabili per i checkpoint TinyStories/llama2.c, e uno split di validazione pulito
(Survey 5: ~30% del validation TinyStories compare nel train).

## Implicazione per FloppyLM

F0 (novità): la tesi non è nuova in astratto. VBQ dimostra già "bigger-but-smaller" su TinyStories e
SeedLM codifica pesi come seed pseudo-casuali; MobileLLM-LS è espansione per ripetizione. La novità
difendibile è solo la combinazione "accounting totale su supporto fisico + regime sub-10M + espansione
procedurale a boot", e va dichiarata così. F1 (procedurale ≤ frontiera densa a pari bit): il bersaglio
da battere non è "2.9M a 4 bit" in astratto ma il migliore tra int8 ~1.4M, 4 bit ~2.6M e ternario ~6–7M,
ciascuno con forma (profondità/larghezza/vocabolario) ottimizzata: Baseline Shape mostra che una forma mal
scelta regala fino al 22% di loss al competitor, quindi un baseline non ottimizzato invalida qualunque
vittoria. Il weight sharing a blocchi rientra nella classe procedurale ma deve essere anche un baseline,
perché è la descrizione procedurale più economica possibile. F2 (vantaggio che sparisce con entropy coding
e pruning sul baseline): è il rischio più concreto, perché i pesi ternari hanno fino al 51% di zeri e BITCOS
o una codifica aritmetica dei pesi quantizzati recuperano 5–15% di byte gratis; ogni tecnica di
compressione lossless dei pesi applicata al procedurale va applicata identica al denso. F3 (costo di boot):
la frontiera densa non ha costo di espansione, quindi ogni secondo di boot è un costo puro del procedurale;
un denso da ~2.6M in C gira a centinaia di tok/s su i7-1165G7, per cui il vincolo ≥5 tok/s pesa solo sul
modello espanso, non sul baseline. F4 (coerenza): a 2.6M il denso è al limite inferiore della coerenza
TinyStories (la coerenza emerge da hidden ≥128 e a ~8M arriva a ~5/10); il procedurale deve quindi
espandere a un modello effettivo ≥10–30M per avere un vantaggio visibile, il che rende F3 stringente.

## Esperimento minimo

E0 costruisce la frontiera densa con byte accounting reale: tre famiglie (int8, 4 bit con gruppi,
ternario QAT) su TinyStories deduplicato e ri-splittato, tokenizer BPE da 256/512/1024/2048, sweep di
forma a budget fisso di 11.2 Mbit, stesso numero di token di training per tutti; si misura bpb held-out,
byte del file pesi + tokenizer + runtime `run.c`-like, e si pubblica la curva bpb-vs-byte, non un punto.
E1 addestra il modello procedurale (seed + coefficienti, sharing, generatore) allo stesso budget di bit
e allo stesso compute, e lo confronta sulla curva di E0. E2 applica a tutti la stessa pipeline di
compressione lossless dei pesi (pruning, codifica entropica/rANS, eventuale rate loss durante il training
per ridurre l'entropia dei pesi) e ricalcola la frontiera: se il vantaggio di E1 scompare, F2 è
confermata. E3 scala i parametri effettivi espansi (10M, 30M, 100M) misurando tempo di espansione, RSS di
picco e tok/s sull'i7-1165G7 per tracciare dove F3 taglia. E4 scrive l'immagine FAT12 reale da
1 474 560 byte con runtime statico, tokenizer e pesi, la avvia da zero su una macchina pulita e ripete le
misure di E0–E3 sul solo contenuto dell'immagine.
