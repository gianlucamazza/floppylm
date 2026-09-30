# Survey 7 — VQ a codebook appreso sotto il bit: learned vs seed vs ternario a pari rate

Consolidato da ricerca web del 2026-09-30.

## Domanda

Esiste già un LM addestrato da zero con pesi quantizzati vettorialmente a codebook appreso sotto 1
bit/peso, e cosa si sa di VQ appreso vs codebook casuale vs ternario a pari rate?

## Cosa esiste

**VQ post-training su LLM grandi (2–3 bit).** Quasi tutta la letteratura VQ sui pesi sta qui. AQLM
([arXiv:2401.06118](https://arxiv.org/abs/2401.06118), ICML 2024) usa quantizzazione additiva con
codebook appresi per blocco: a ~2 bit usa un codebook da 2^15–2^16 voci su gruppi di 8 pesi e porta
Llama-2 7B da 5.12 a 6.59 e il 70B da 3.12 a 3.94 di ppl WikiText-2. Il costo di calibrazione è di
~1 giorno A100 per il 7B, più 3–6 h di fine-tuning su 4 A100. Il codebook FP16 costa g·2^B·16 bit per
matrice, trascurabile a 7B, non a 1.44 MB. GPTVQ ([arXiv:2402.15319](https://arxiv.org/abs/2402.15319))
mostra la "benedizione della dimensionalità": a pari bit, VQ a dimensione più alta domina lo scalare.
Il codebook viene inizializzato con EM data-aware e compresso con int8 e SVD, al costo di 3–11 h H100
per il 70B. VPTQ ([arXiv:2409.17066](https://arxiv.org/abs/2409.17066)) è VQ del secondo ordine a 2 bit:
−0.01/−0.34 ppl su Llama-2 rispetto allo SOTA, throughput 1.6–1.8× migliore. LCQ
([arXiv:2405.20973](https://arxiv.org/abs/2405.20973)) sostituisce il codebook di rango uno con uno a
rango basso e dichiara costo di memorizzazione "trascurabile". GLVQ
([arXiv:2510.20984](https://arxiv.org/abs/2510.20984)) apprende per gruppo la matrice generatrice di un
reticolo e contiene l'unica ablazione pulita appreso-vs-fisso trovata. Con un reticolo fisso condiviso
la ppl di Llama-2 7B a 2 bit sale da 5.69 a 5.95; a 1.0 bit medio GLVQ fa 7.83, contro 32.48 di BiLLM,
9.73 di OneBit e 8.28 di PV-Tuning. La decodifica on-the-fly a sotto-blocchi costa il 2–3% di latenza
rispetto a int4.

**Codebook fissi o calcolati: il braccio "seed" esiste già, ed è forte.** QuIP#
([arXiv:2402.04396](https://arxiv.org/abs/2402.04396)) usa un codebook non appreso, il reticolo E8
(E8P, 8 dimensioni, 2 bit), dopo una trasformata di Hadamard casuale che rende i pesi quasi gaussiani
i.i.d. QTIP ([arXiv:2406.11235](https://arxiv.org/abs/2406.11235), NeurIPS 2024 spotlight) sostituisce
il VQ con quantizzazione a traliccio (bitshift trellis, L=16), che separa rate e dimensione e arriva a
dimensione effettiva 256. È il dato più importante per la nostra ablazione. I codici _calcolati_ 1MAD e
3INST generano valori pseudo-gaussiani da un LCG in 2–4 istruzioni e non hanno parametri. Su sorgente
gaussiana a 2 bit fanno MSE 0.069, contro 0.071 del codice ibrido _tunabile_ HYB, 0.089 dell'E8P
di QuIP# e 0.063 del limite distorsione-rate. Su Llama-2 senza fine-tuning, a 2 bit, 1MAD e 3INST danno
ppl identiche: 6.82 sul 7B e 3.90 sul 70B, contro 8.22 e 4.16 di QuIP#, con 23.5 tok/s sul 70B
(RTX 6000 Ada). SeedLM ([arXiv:2410.10714](https://arxiv.org/abs/2410.10714)), già discusso nella
[Survey 2](02-procedural-weights.md), è il codebook casuale per blocco (seed LFSR più coefficienti),
ma resta a 3–4 bit. Sui pesi gaussianizzati, quindi, un codice pseudo-casuale ad alta dimensione
eguaglia o batte un codebook appreso a bassa dimensione, e costa 0 byte.

**Sotto il bit: tutto post-training o QAT su modelli preaddestrati.** BiLLM
([arXiv:2402.04291](https://arxiv.org/abs/2402.04291)) arriva a 1.08 bit medi (Llama-2 70B ppl 8.41)
con 0.5 h per un 7B. PB-LLM ([arXiv:2310.00034](https://arxiv.org/abs/2310.00034)) binarizza tutto
tranne una frazione di pesi salienti tenuta a bit più alti. OneBit
([arXiv:2402.11295](https://arxiv.org/abs/2402.11295), NeurIPS 2024) usa segni ±1 più vettori di valori
con distillazione e conserva ≥81% delle prestazioni di LLaMA. STBLLM
([arXiv:2408.01803](https://arxiv.org/abs/2408.01803)) è la prima binarizzazione strutturata N:M sotto
il bit. Su LLaMA-2 7B (FP16 5.47) dà 13.06 a 0.8 bit, 18.74 a 0.7 e 27.93 a 0.55, contro 50.25 e 263.61
di BiLLM; sul 65B (FP16 3.53) fa 6.43 a 0.8 bit e 11.07 a 0.55. BTC-LLM
([arXiv:2506.12040](https://arxiv.org/abs/2506.12040)) è il più vicino al nostro meccanismo. Raggruppa i
vettori _binari_ ricorrenti in un codebook binario appreso (centroidi aggiornati per segno, indici
compatti), fra 0.7 e 1.11 bit, e perde 3.1 punti zero-shot a 0.8 bit su LLaMA-2 13B. NanoQuant
([arXiv:2602.06694](https://arxiv.org/abs/2602.06694)) fattorizza in matrici binarie a rango basso via
ADMM (70B compresso 25.8× in 13 h H100). LittleBit
([arXiv:2506.13771](https://arxiv.org/abs/2506.13771)) fa QAT su fattori latenti binarizzati fino a
0.1 bit/peso e dichiara che a 0.1 bpw su Llama-2 7B batte il miglior metodo a 0.7 bpw. Il messaggio
comune è che sotto il bit la ppl esplode anche a 7–65B con PTQ, e che funziona solo ciò che fattorizza
(rango basso binario) o riusa strutture ricorrenti (codebook binario). Nessuno di questi addestra da zero.

**Da zero: 1 bit sì, VQ quasi mai.** BitNet ([arXiv:2310.11453](https://arxiv.org/abs/2310.11453))
addestra da zero pesi a 1 bit con BitLinear e mostra una scaling law simile al FP16. Il ternario b1.58 e
i suoi limiti sotto 1B sono coperti nelle Survey [1](01-tiny-lms.md) e [3](03-mdl-compression.md). Il
controesempio più vicino alla tesi v0.2 è Quant-Noise (Fan, Stock et al.,
[arXiv:2004.07320](https://arxiv.org/abs/2004.07320), ICLR 2021). Un Transformer a 16 layer su
WikiText-103 viene addestrato _da zero_ quantizzando a ogni forward un sottoinsieme casuale di blocchi
(noise 0.05, blocchi da 8) e poi compresso con iPQ (PQ iterativo alla Stock). Si passa da 942 MB (ppl
18.3) a 38 MB (ppl 20.7, contro 25.2 senza Quant-Noise): ×24.8, cioè ~1.3 bit/peso. Con condivisione dei
layer arriva a 19 MB e ppl 22.0 (×49.5, ~0.65 bit per peso effettivo); con pruning 10 MB e ppl 24.7 (×94,
~0.34). Il dato chiave per il training è che la QAT con straight-through integrale su iPQ è _peggiore_
del PTQ: ppl 41.2 contro 25.2. Il codebook però è k-means post-hoc, non appreso sotto loss di rate, la
scala è 247M con vocabolario da 267k, e non c'è controllo con codebook casuale. Stock et al.
([arXiv:1907.05686](https://arxiv.org/abs/1907.05686), ICLR 2020) sono il PQ di riferimento dei pesi:
ResNet-50 in 5 MB (×20, ~1.6 bit/peso) al 76.1% top-1, Mask R-CNN ×26, solo visione. DKM
([arXiv:2108.12659](https://arxiv.org/abs/2108.12659), ICLR 2022) rende differenziabile il k-means con
attenzione peso→centroide e congiunge pesi e centroidi. Ottiene MobileNet-v1 in 0.72 MB (63.9%) e
DistilBERT ×11.8 con −1.1% su GLUE, ma la memoria del training è proibitiva per LLM: eDKM
([arXiv:2309.00964](https://arxiv.org/abs/2309.00964)) la riduce di 130× per portare LLaMA-7B a 3 bit,
sempre da preaddestrato. Soft-to-Hard VQ ([arXiv:1704.00648](https://arxiv.org/abs/1704.00648)) è il
precursore "VQ + entropia annealing" della loss MDL (Survey 3), solo su visione. Sign Lock-In
([arXiv:2602.17063](https://arxiv.org/abs/2602.17063), ICML 2026) è l'unico lavoro da zero sotto il bit
su testo che ho trovato. Mostra che i segni dei pesi restano quelli dell'inizializzazione casuale, perché
i flip avvengono solo per rari attraversamenti vicino a zero, e che sotto 1 bpw i segni sono il collo di
bottiglia incomprimibile. Addestrando da zero con un template di segni a rango 2 regenerabile, un CharLM
tiene la ppl a ~0.5–0.7 bpw e i flip scendono a ~10⁻³ per circa +1 punto di ppl. Non è VQ, ma è evidenza
diretta che una parte della descrizione sotto il bit può venire da un seed.

**Appreso vs casuale fuori dai pesi di LM.** L'evidenza è divisa. Variable Bitrate Neural Fields
([arXiv:2206.07707](https://arxiv.org/abs/2206.07707), SIGGRAPH 2022) trova che gli indici appresi (VQ
auto-decoder) richiedono molti meno bit dell'hashing casuale a pari qualità, fino a 100× meno memoria.
Random Entity Quantization ([arXiv:2310.15797](https://arxiv.org/abs/2310.15797), EMNLP 2023) trova
invece che assegnare codeword casuali alle entità di un KG eguaglia le strategie apprese, perché i codici
casuali hanno più entropia e distinguibilità. FSQ ([arXiv:2309.15505](https://arxiv.org/abs/2309.15505))
mostra che un codebook _fisso_ (griglia scalare a poche dimensioni) eguaglia il VQ appreso nei VQ-VAE
senza collasso e senza loss di commitment, reseeding o penalità di entropia. "Only relative ranks matter"
([arXiv:2603.17917](https://arxiv.org/abs/2603.17917)) clusterizza Llama-3.1-8B e SmolLM2-135M a 16–64
valori per matrice. Randomizzare i centroidi preservando l'ordine non costa quasi nulla nei layer medi e
tardi; rimescolare i ranghi distrugge il modello; il fine-tuning dei centroidi recupera solo il 30–40%
del gap residuo. I valori esatti del codebook contano quindi poco, la sua struttura molto.

**Embedding (28% dei bit a d=384, V=2048).** Shu & Nakayama
([arXiv:1711.01068](https://arxiv.org/abs/1711.01068), ICLR 2018) apprendono end-to-end codici
composizionali multi-codebook via Gumbel-softmax: −98% sull'embedding in sentiment, −94–99% in
traduzione. DPQ ([arXiv:1908.09756](https://arxiv.org/abs/1908.09756), ICML 2020) rende differenziabile
il PQ dell'embedding, drop-in, con ×14–238 a costo trascurabile. CARVQ
([arXiv:2510.12721](https://arxiv.org/abs/2510.12721), EMNLP Findings 2025) fa RVQ di gruppo più un
piccolo MLP correttivo, post-training, quasi senza perdita a ~2.4 bit e usabile a ~1.6. VQ-Logits
([arXiv:2505.10202](https://arxiv.org/abs/2505.10202)) dichiarava −99% sull'output layer con +4% di
ppl, ma è stato ritirato il 18/9/2026 per esperimenti insufficienti e non va usato. Il lavoro sui codici
binari fissi in ingresso ([arXiv:2605.09751](https://arxiv.org/abs/2605.09751)) è già in Survey 2: sul
lato input il codebook casuale è gratis e non perde nulla.

**Parameter Golf** ([repo](https://github.com/openai/parameter-golf)), tutto a 16 MB. PR
[#1433](https://github.com/openai/parameter-golf/pull/1433) "Codebooks!" usa il codebook E8P fisso di
QuIP#, scelto proprio per non dover memorizzare il codebook ("risparmia 1–2 MB"). Indici a 16 bit su
blocchi da 8 più scala a 8 bit fanno 3.0 bpw, e il gap di quantizzazione resta grande (pre-quant 1.104,
post 1.224, 1.2067 sliding su 3 seed). L'autore riporta che scendere sotto 2 bpw dà modelli incoerenti,
che codebook multipli o residui alla AQLM sono difficili da ottimizzare, e che la QAT con VQ nel forward
è troppo lenta. Nota anche che la penalità di entropia sull'assegnazione riduce i byte ma danneggia di
più, e che il semplice "snapping" periodico al codebook funziona meglio di metodi più sofisticati. PR
[#1335](https://github.com/openai/parameter-golf/pull/1335) co-addestra un codebook VQ (G=2, K=1024,
sfera, EMA 0.95, reseeding delle voci morte) durante il warmdown, a 5 bpw. Il delta di quantizzazione è
+0.0018 bpb, contro +0.0024 del k-means post-hoc e +0.0049 di INT5: l'appreso-in-training batte il
post-hoc solo di 0.0006 bpb. PR [#212](https://github.com/openai/parameter-golf/pull/212) misura che il
k-means K=256 ha MSE −87% rispetto a int6 ma produce un artefatto +25% più grande dopo zstd, perché gli
indici hanno entropia alta. PR [#532](https://github.com/openai/parameter-golf/pull/532) recupera il 21%
con codebook per tensore più Huffman. PR [#1515](https://github.com/openai/parameter-golf/pull/1515)
(k-means pesato con la Hessiana a int3) fa 1.0872 e mostra un pavimento dello scalare a 16 MB. Sul
binario da zero, PR [#2048](https://github.com/openai/parameter-golf/pull/2048) fa 1.3551 e l'XNOR-Net di
[#1388](https://github.com/openai/parameter-golf/pull/1388) 1.539. Nessuna PR fa VQ sotto il bit, né
appreso né casuale, né VQ da zero.

## Cosa manca

Query web: "language model trained from scratch vector quantized weights learned codebook sub-1-bit",
"quantization-aware training vector quantization codebook transformer weights from scratch", "sub-1-bit
LLM compression 2025", "weight clustering k-means codebook trained from scratch small language model
TinyStories", "vector quantized weights pretraining LLM codebook 2026", "sub-1-bit language model
pretraining from scratch", "learned codebook versus random codebook equal bitrate", "random fixed
codebook vs learned codebook LLM ablation". Su Parameter Golf ho cercato con `gh pr list --state all` i
termini vector quantization, VQ, codebook, k-means, kmeans, product quantization, lattice, E8, trellis,
QTIP, AQLM, clustering, sub-bit, binary, "codebook QAT", "random codebook".

Il contro-esempio pieno non esiste. Nessun lavoro addestra da zero un LM piccolo (≤30M) con pesi VQ a
codebook appreso sotto 1 bit/peso, e nessuno confronta a pari rate, con i byte del codebook contati,
codebook appreso vs codebook da seed vs ternario. I pezzi esistono separati. Da zero ci sono binario
(BitNet), sub-bit non-VQ (Sign Lock-In, CharLM) e PQ a ~1.3 bit con rumore ma codebook post-hoc
(Quant-Noise). Sub-bit con codebook appreso c'è solo post-training (BTC-LLM, GLVQ a 1.0 bit). Il
confronto appreso-vs-calcolato c'è solo post-training a 2 bit, e lì il calcolato vince o pareggia
(QTIP); l'unica ablazione in senso opposto è GLVQ (+0.26 ppl col reticolo fisso), sempre post-training.
Manca anche il conto dei byte del codebook nel regime in cui pesa. Con 11 Mbit, un codebook FP16
da 2^16 × 8 (quello di AQLM) costa da solo 8 Mbit.

## Implicazione per FloppyLM

**F0.** Vedi verdetto. La combinazione "VQ appreso + da zero + sotto il bit + LM minuscolo + controllo
seed a pari rate + ricorsione" è nuova; nessuno dei suoi componenti lo è.

**F1** (learned VQ + ricorsione non batte di ≥max(0.02, 2σ) il migliore fra denso ternario/2-bit e
ricorsione ternaria a pari byte). Il prior è sfavorevole per tre motivi. Primo, sotto il bit la ppl PTQ
esplode anche a 7–65B (STBLLM 0.55 bit: ×5 la ppl del 7B), e da zero l'unico LM sub-bit (Sign Lock-In)
resta sul CharLM. Secondo, Parameter Golf non ha chiuso il gap VQ nemmeno a 3 bpw (#1433: +0.12 bpb) e ha
trovato binario e XNOR nettamente peggiori di int6. Terzo, in Quant-Noise il passo sotto il bit per peso
effettivo arriva dalla _condivisione_ (19 MB, ppl 22.0), non da un PQ più aggressivo. L'argomento a
favore è che il ternario a 1.58 bit dà ~7M parametri, mentre a 0.5 bpw i ~7 Mbit del core valgono ~14M
pesi, ×4 con la ricorsione.

**F1-ablazione (appreso ≈ seed).** È probabile che scatti, ed è il risultato più informativo della
survey. QTIP mostra che su pesi gaussianizzati un codice pseudo-casuale calcolato eguaglia quello
tunabile (MSE 0.069 vs 0.071, ppl identiche fra 1MAD e 3INST). FSQ e Random Entity Quantization
mostrano lo stesso fuori dai pesi, e "Only relative ranks matter" che i valori esatti dei centroidi
contano poco. In più, da zero i pesi _co-adattano_ al codebook: la QAT sposta i pesi verso le celle
disponibili, e questo erode il vantaggio di un codebook su misura, che nel PTQ esiste solo perché i
pesi sono fissati prima. Infine il codebook appreso paga byte che il seed non paga. A rate R = log₂K/d
costa K·d·b_c bit: a R=0.5 con d=16, K=256 e b_c=8 sono 4 KB (trascurabile), ma con d=24, K=4096 sono
~98 KB, il 7% del floppy. Il VQ ad alta dimensione, dove GPTVQ e QTIP dicono che sta il guadagno, è
accessibile a costo zero solo con codici calcolati. Il braccio appreso va quindi strutturato:
codebook unico condiviso fra layer (#1433 trova che la condivisione funziona), generatore di
reticolo alla GLVQ o rango basso alla LCQ. Un K libero per layer non regge.

**F2** (il vantaggio sparisce con la stessa codifica entropica per tutti). Il rischio è concreto e
asimmetrico. Gli indici VQ hanno entropia quasi massima: #212 trova indici k-means _meno_ comprimibili
di int6 sotto zstd, e #1433 che forzare il riuso dei codici costa qualità. Il ternario invece guadagna
dalla codifica perché è sparso (BITCOS 1.485 bit, Survey 3). Il VQ quindi incassa poco da E2, i
baseline molto, e il confronto va fatto su byte codificati, non su bit nominali.

**F3** (boot). Non è una minaccia. La decodifica VQ è un gather: N/d letture di tabella, cioè 14M
pesi a d=16 fanno <1M gather, millisecondi. Un codebook da seed richiede K·d estrazioni PRNG (≤10⁵),
un codice calcolato alla QTIP 2–4 istruzioni per peso senza tabella. L'espansione in fp32 di 14M
pesi occupa 56 MB di RSS, ma si può evitare decodificando on-the-fly a sotto-blocchi (GLVQ: 2–3% di
latenza, picco di memoria ÷10). Con la ricorsione il costo si paga una sola volta per blocco condiviso.

**F4** (coerenza). Il VQ non tocca F4 direttamente, ma se F1 scatta i parametri effettivi restano ~7M
e la soglia di coerenza TinyStories (10–30M, Survey 1) resta fuori portata.

**Costo del training VQ-QAT.** Il VQ-VAE classico (commitment β≈0.25, EMA dei centroidi) collassa: le
voci morte vanno reinizializzate (#1335 le rimpiazza dopo 5 snap inutilizzati), e le cause note sono il
bias dello straight-through, gli aggiornamenti "un passo indietro" e i gradienti sparsi del codebook
([arXiv:2509.10140](https://arxiv.org/abs/2509.10140)). Il rotation trick
([arXiv:2410.06424](https://arxiv.org/abs/2410.06424)) migliora gradienti e utilizzo, FSQ elimina il
problema fissando il codebook. Sui pesi, lo STE pieno può essere peggiore del PTQ (Quant-Noise 41.2 vs
25.2), mentre quantizzare un sottoinsieme casuale per passo costa <5% di tempo. L'assegnazione
nearest-neighbor costa N·K flop per passo, cioè 5.7·10¹⁰ con N=14M e K=4096, ~3% del forward di un passo
da 64k token (2·N·T ≈ 1.8·10¹² flop): accettabile, ma su questo laptop meglio ogni k passi. DKM completo
richiede memoria O(N/d·K), che eDKM ha dovuto ridurre di 130×.

**Cosa cambia per la tesi v0.2.** (1) Il braccio di controllo seed non è una baseline debole ma il
favorito a priori. Conviene preregistrare che la tesi "codebook appreso" vale solo se batte il seed di
≥2σ _includendo i byte del codebook_. (2) Serve un terzo braccio a codice calcolato ad alta dimensione
(traliccio bitshift QTIP, rate frazionari senza tabella), perché domina il VQ a 8D a pari rate. (3) La
ricetta di training deve prevedere Quant-Noise o snapping periodico con reseeding, non STE puro. (4)
Sotto il bit i segni sono il collo di bottiglia: segni da template seed (Sign Lock-In) più magnitudini
VQ è un ibrido naturale fra seed e appreso da provare. (5) Per l'embedding la letteratura dà già
×14–238 con PQ/codici composizionali appresi e input casuale gratis: il 28% dell'embedding è il bersaglio
più facile, ma non è la novità.

## Esperimento minimo

È un E1 ristretto, prima di E2. Su TinyStories con V=2048, d=384 e un budget core fisso di 7 Mbit
(byte esatti inclusi codebook, scale e indici), 3 seed e 3 rate (0.5, 0.75, 1.0 bpw), si addestrano da
zero con la stessa ricorsione (k blocchi condivisi × r iterazioni) cinque bracci:

- (a) VQ con codebook appreso unico condiviso (d=8/16, K=2^(Rd), EMA più reseeding, Quant-Noise p=0.05);
- (b) lo stesso VQ con codebook da seed congelato (gaussiano, stessa scala per riga);
- (c) traliccio calcolato 1MAD/3INST alla QTIP;
- (d) ternario QAT a pari byte;
- (e) 2-bit QAT a pari byte, questi due come baseline F1.

Si misura bpb su validazione, byte codificati (anche con rANS per tutti, anticipando E2), tempo di
assegnazione per passo e tempo di boot/decodifica sul binario C. F1-ablazione scatta se |a−b| <
max(0.02, 2σ) a tutti i rate; F1 scatta se min(a, b, c) non batte min(d, e) di max(0.02, 2σ). Se (b) o
(c) ≥ (a), la tesi si riscrive come "VQ da seed + ricorsione" e il codebook appreso si riduce ad
ablazione.

**Verdetto F0: parziale.** Non scatta pienamente. Nessun lavoro trovato addestra da zero un LM con pesi
VQ a codebook appreso sotto 1 bit/peso, e nessuno confronta appreso e seed a pari rate contando i byte
del codebook, tanto meno in un LM minuscolo con ricorsione. Non si può però dire "non scatta". I
singoli pezzi sono pubblicati e vanno citati come stato dell'arte:

- Quant-Noise: LM da zero PQ-aware a ~1.3 bit, ~0.65 per peso effettivo con sharing;
- Sign Lock-In: LM da zero a 0.5–0.7 bpw, con i segni da template;
- BTC-LLM e GLVQ: codebook appreso a 0.7–1.0 bit, post-training;
- QTIP: codice casuale calcolato ≈ codebook tunabile;
- Parameter Golf #1335 e #1433: codebook co-addestrato o fisso su LM, a 3–5 bpw.

La novità rivendicabile è il confronto controllato a byte esatti nel regime sotto 1.5 MB, non il
meccanismo. Il prior della letteratura è che il codebook appreso _non_ batterà quello da seed.
