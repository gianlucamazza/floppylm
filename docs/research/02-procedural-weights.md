# Survey 2 — Pesi procedurali, seed e condivisione: esiste già un FloppyLM?

Consolidato da ricerca web del 2026-09-30.

## Domanda

Esiste già un LM addestrato da zero la cui descrizione totale (pesi + tokenizer + runtime) sta in ≤1.44
MB (1 474 560 byte) sfruttando l'asimmetria bit-a-riposo / RAM-a-runtime, cioè memorizzando una
descrizione corta di un modello effettivo molto più grande?

## Cosa esiste

**Famiglia "combinazione lineare di basi pseudo-casuali".** PRANC
([arXiv:2206.08464](https://arxiv.org/abs/2206.08464), ICCV 2023) riparametrizza un'intera rete come
combinazione lineare di reti casuali congelate generate da un unico seed; si addestrano solo i
coefficienti, da zero, e i pesi si rigenerano layer per layer a inferenza. È esattamente il meccanismo di
FloppyLM, ma è validato solo su classificazione di immagini (ResNet piccole, ~100× di compressione) e
rappresentazioni implicite, mai su un LM. NOLA ([arXiv:2310.02556](https://arxiv.org/abs/2310.02556),
ICLR 2024) porta la stessa idea sulle matrici LoRA: coefficienti su basi casuali congelate, fino a ~20×
più compatto del LoRA rank-1 su LLaMA-2 70B; è fine-tuning di un modello denso preesistente, quindi la
descrizione totale include il backbone. MCNC ([arXiv:2406.19301](https://arxiv.org/abs/2406.19301), ICLR 2025) sostituisce il sottospazio lineare con una varietà non lineare generata da un MLP sinusoidale
congelato: addestra da zero ResNet/DeiT-Ti su CIFAR e ImageNet-100 e fa PEFT su LLaMA-2 (25k parametri,
45.8 MMLU), e gli autori scrivono esplicitamente di non aver mostrato l'effetto di MCNC "nel training di
LLM da zero, che potrebbe essere l'impatto più importante". Kilobyte Models
([arXiv:2608.00860](https://arxiv.org/abs/2608.00860), agosto 2026) formalizza "rete = seed + latente
quantizzato + normalizzazioni" con base a blocchi seedata e QAT, ottenendo 98.6% su MNIST in 2 KB e un
adapter ResNet-50 in 4 KB; anche qui gli autori dichiarano che il metodo "non è ancora esteso a
Transformer e LLM".

**Famiglia "seed per blocco, post-training".** SeedLM (Apple,
[arXiv:2410.10714](https://arxiv.org/abs/2410.10714), ICLR 2025) comprime LLM già addestrati: per ogni
blocco di 8–12 pesi cerca per forza bruta uno fra 2^16−1 seed di un LFSR, la cui matrice casuale
combinata con 3–4 coefficienti a 4 bit e un esponente condiviso a 4 bit ricostruisce il blocco, a 3–4
bit/peso (Llama 3 70B: WikiText-2 ppl 2.9 FP16 → 3.8 a 4 bit, 5.7 a 3 bit). Dimostra che un LFSR è un
generatore economico in hardware e che il trade calcolo-per-memoria funziona, ma non scende sotto ~3
bit/peso, non è addestramento da zero e non rende il modello effettivo più grande di quello memorizzato.
Hyper-Compression ([arXiv:2409.00592](https://arxiv.org/abs/2409.00592)) rappresenta i parametri con
traiettorie di sistemi dinamici ergodici, post-hoc, a prestazioni vicine a int4 su LLaMA/Qwen. Neural
Weight Compression ([arXiv:2510.11234](https://arxiv.org/abs/2510.11234)) apprende un codec neurale per i
pesi di LM, forte nel regime 4–6 bit. Tutti operano su modelli già addestrati.

**Hashing e hypernetwork.** HashedNets ([arXiv:1504.04788](https://arxiv.org/abs/1504.04788)) condivide
pesi tramite hash: nessun indice memorizzato, fino a 1/64 su MNIST; è il precursore diretto del "modello
effettivo grande, parametri liberi pochi". HyperNetworks
([arXiv:1609.09106](https://arxiv.org/abs/1609.09106)) genera pesi con una rete ausiliaria; su enwik8 la
HyperLSTM arriva a ~1.34 bpc, ma per LM la hypernetwork è usata per pesi dinamici, non per ridurre i byte
a riposo. Irie & Schmidhuber ([arXiv:2112.15545](https://arxiv.org/abs/2112.15545)) addestrano LSTM
carattere-livello su enwik8 con matrici parametrizzate da coefficienti DCT: è il precedente più vicino di
"LM addestrato in uno spazio di pesi compresso", su scala piccola e senza contabilità dei byte totali.

**Condivisione di pesi e profondità ricorrente.** ALBERT
([arXiv:1909.11942](https://arxiv.org/abs/1909.11942)) e Universal Transformers
([arXiv:1807.03819](https://arxiv.org/abs/1807.03819)) sono la forma più semplice di "descrizione corta,
modello effettivo profondo". Relaxed Recursive Transformers
([arXiv:2410.20672](https://arxiv.org/abs/2410.20672), ICLR 2025) convertono Gemma 2B in un ricorsivo da
1B con LoRA per profondità che batte TinyLlama 1.1B e Pythia 1B, ma partendo da pesi preaddestrati.
Mixture-of-Recursions ([arXiv:2507.10524](https://arxiv.org/abs/2507.10524)) addestra da zero ricorsivi
da 135M a 1.7B e, a parità di FLOP e con meno parametri unici, migliora perplexity e few-shot rispetto a
vanilla e ricorsivi semplici. È la famiglia con la migliore evidenza positiva da zero per LM, ma nessun
lavoro la misura in byte totali sotto 2 MB.

**Dimensione intrinseca e reti casuali congelate.** Li et al.
([arXiv:1804.08838](https://arxiv.org/abs/1804.08838)) addestrano da zero in sottospazi casuali: d_int90
≈ 750 per un MLP MNIST e 290 per una LeNet, cioè seed + 750 float, compressione ~150–260×; notano che il
90% della prestazione è una soglia debole. Aghajanyan et al.
([arXiv:2012.13255](https://arxiv.org/abs/2012.13255)) mostrano che 200 parametri proiettati bastano a
portare RoBERTa al 90% su MRPC, ma nel fine-tuning: la dimensione intrinseca è bassa proprio perché il
preaddestramento ha già fatto il lavoro, quindi non si trasferisce al training da zero. Sul lato "casuale
congelato", Shen et al. ([arXiv:2109.03939](https://arxiv.org/abs/2109.03939)) trovano supermask in un
Transformer a un layer casuale che raggiungono 29.45 BLEU su IWSLT14; Zhong & Andreas
([arXiv:2410.04368](https://arxiv.org/abs/2410.04368), NeurIPS 2024) mostrano che Transformer casuali con
solo embedding/unembedding addestrati imparano aritmetica modulare, recall associativo e "alcuni aspetti"
di generazione di testo. Sul tokenizer, [arXiv:2605.09751](https://arxiv.org/abs/2605.09751) sostituisce
la tabella di embedding in ingresso con codici binari fissi senza perdita misurabile (ppl 2.36 vs 2.44,
entro la varianza fra seed), il che rende la tabella di input gratuita in byte.

**Il controesempio più vicino: OpenAI Parameter Golf (marzo–aprile 2026).** La sfida
([repo](https://github.com/openai/parameter-golf), analisi
[arXiv:2607.01517](https://arxiv.org/abs/2607.01517)) chiede il miglior LM con artefatto ≤16 MB contando
codice + pesi compressi, valutato in bpb su FineWeb, con 10 minuti su 8×H100 (più un track non-record a
calcolo illimitato). OpenAI ha messo esplicitamente "Learning adapters on random linear maps" fra le
richieste di PR. Ne sono nati proprio gli esperimenti di FloppyLM, in un regime di byte 11× più largo. PR
[#1113](https://github.com/openai/parameter-golf/pull/1113): matrici ortogonali casuali rigenerate da
seed (0 byte) + LoRA rank 32, 29.7M parametri effettivi di cui 3.74M memorizzati, artefatto 5 191 021
byte, 1.3705 bpb. PR [#1753](https://github.com/openai/parameter-golf/pull/1753): rete congelata da un
uint32 seed + supermask binarie apprese (~118M bit di maschera) + scale fp16, 14.9 MB, 1.2917 bpb dopo 57
h su A100; nota che i bit di maschera sono quasi incomprimibili. PR
[#2058](https://github.com/openai/parameter-golf/pull/2058) (adapter rank 160 su MLP casuali, entro 16
MB) arriva a 1.1971; PR [#1710](https://github.com/openai/parameter-golf/pull/1710) usa MLP a feature
casuali (proiezione di ingresso da seed) dentro uno stack competitivo da 13.4 MB. PR
[#336](https://github.com/openai/parameter-golf/pull/336) prototipa una hypernetwork a tronco condiviso
che genera 26.5M parametri GPT da 2.8M (2.09 MB) senza riportare bpb. PR
[#1589](https://github.com/openai/parameter-golf/pull/1589) documenta fallimenti sistematici su 1×H100 in
10 minuti: "seed model" θ = θ₀ + P·φ con φ ∈ R^2048 (547k parametri memorizzati, espansione 8064×) non
completa nemmeno la prima validazione perché generare P a blocchi domina il passo; generatore SIREN
coordinate→peso 5.12 bpb; automa cellulare neurale 4.16; hypernetwork rank 32 2.74. Il confronto quasi
appaiato più istruttivo è dello stesso autore con la stessa pipeline: Universal Transformer 3 blocchi × 4
iterazioni, PR [#1110](https://github.com/openai/parameter-golf/pull/1110), 4 946 680 byte, 1.2249 bpb,
contro random maps + LoRA a 5.19 MB, 1.3705 bpb. A byte quasi uguali la condivisione di pesi batte i pesi
da seed di 0.15 bpb.

**Floppy come vincolo esplicito.** Il 13 settembre 2026 un contributore HF ha pubblicato "Single Floppy
346K" ([resoconto](https://runtimewire.com/article/nilky-single-floppy-346k-language-model-raspberry-pi),
[modello](https://huggingface.co/NILKNARFGonzo/single-floppy-346k)): un LM denso da 346k parametri
pensato per stare su un floppy, dichiarato peggiore di un modello da 1k, senza metrica né contabilità dei
byte. Anche lo stories260K di llama2.c (≈1.06 MB FP32) sta già su un floppy. "Un LM su un floppy" in sé
non è quindi nuovo; la novità possibile sta solo nel rapporto qualità/byte.

## Cosa manca

Ho cercato attivamente controesempi con queste query e fonti: "language model fits on a floppy disk",
"procedurally generated weights language model from scratch", "seed-based weight generation LLM 2026",
"pretraining in random subspace / random basis coefficients", "hypernetwork generates transformer weights
compression", "demoscene 64k neural network", "description length under 1 MB TinyStories", più ricerca
mirata nelle PR di Parameter Golf (hypernetwork, seed, random weights, procedural, PRNG, floppy,
1MB/2MB/4MB, ternary, entropy). Il risultato è netto su quattro punti.

Primo, la letteratura accademica sulle basi pseudo-casuali (PRANC, NOLA, MCNC, Kilobyte Models) non ha
mai addestrato un LM da zero, e due di questi lavori lo dichiarano esplicitamente come limite. Secondo, i
lavori su LLM con seed (SeedLM, Hyper-Compression, NWC) sono post-training e restano a ≥3 bit/peso sul
modello memorizzato, senza espansione a un modello effettivo più grande. Terzo, Parameter Golf ha già
testato l'idea centrale su LM reali. Non l'ha però testata nel regime di FloppyLM: budget 16 MB invece di
1.44, vincolo di 10 minuti che penalizza proprio l'espansione dei pesi (i fallimenti di #1589 sono da
calcolo, non da bit), coefficienti procedurali non codificati entropicamente (#1113 spende ~10.9 bit per
parametro memorizzato, 5.1 MB per 3.74M parametri), nessuna loss rate-aware sui coefficienti, nessuna
misura del costo di boot, valutazione FineWeb invece di coerenza tipo TinyStories. Quarto, nessun lavoro
trovato confronta a parità esatta di byte totali, con codifica entropica per tutti, un modello
procedurale contro un denso ternario/2-bit più una variante con condivisione dei pesi sotto 1.5 MB.

Il gap residuo è quindi stretto e preciso: un LM addestrato da zero, descrizione totale ≤1 474 560 byte
inclusi tokenizer e runtime, con parametri effettivi ≫ bit memorizzati, addestrato con loss MDL sui bit
della descrizione, confrontato alla pari con denso a basso bit e con condivisione di pesi. L'idea "pesi
da seed + adapter per un LM sotto vincolo di byte" non è nuova; resta aperto solo se funzioni sotto 1.5
MB e meglio delle alternative.

## Implicazione per FloppyLM

Condizioni toccate. **F0 (novità)**: vedi verdetto sotto. **F1**: l'unico confronto quasi appaiato
esistente (#1110 contro #1113, ~5 MB) va contro la tesi: la ricorsione di profondità batte i pesi da seed

- LoRA di 0.15 bpb. È un solo seed, a 10 minuti e con coefficienti non ottimizzati in bit, quindi non
  uccide F1, ma sposta l'onere della prova. **F3**: #1589 mostra che l'espansione densa θ₀ + P·φ con P
  esplicita è proibitiva; servono generatori strutturati (LFSR per blocco come SeedLM, Fastfood/Hadamard,
  Kronecker) generati una volta al boot e non a ogni passo, come notava già Li 2018. **F2**: PRANC/MCNC
  confrontano contro pruning e quantizzazione, mai contro un denso con la stessa codifica entropica. Ne
  segue che la tesi va riformulata: "procedurale" deve includere la condivisione di pesi (ricorsione più
  LoRA per profondità, famiglia Relaxed Recursive/MoR) come braccio principale, non come baseline. Le basi
  da seed vanno viste come un'aggiunta ortogonale (feature casuali gratis in MLP, codici binari fissi per
  l'input), non come sostituto integrale dei pesi.

**Verdetto F0: parziale.** Non scatta pienamente perché nessun lavoro trovato addestra da zero un LM con
descrizione totale ≤1.44 MB e modello effettivo ≫ bit memorizzati, con loss rate-aware e boot misurato;
la letteratura accademica lo lascia esplicitamente aperto (MCNC, Kilobyte Models). Non si può però dire
"non scatta": Parameter Golf ha pubblicamente formulato e implementato la stessa idea di fondo (seed →
pesi congelati → adapter appresi, 30M effettivi in 5.19 MB; supermask su rete da seed; hypernetwork 26.5M
da 2.09 MB). La rivendicazione di novità deve quindi restringersi al regime (sotto 1.5 MB, artefatto
avviabile completo, FAT12 reale), al metodo (training MDL dei coefficienti con entropy coding, confronto
a parità di byte contro denso ternario e ricorsivo) e alla misura (costo di boot e coerenza TinyStories),
e deve citare Parameter Golf come stato dell'arte più vicino.

## Esperimento minimo

Il gap si attacca con E0+E1 a scala ridotta prima di tutto il resto. E0 costruisce la frontiera densa su
TinyStories con contabilità byte-esatta: denso int4/ternario e ricorsivo alla Universal Transformer (3
blocchi × k iterazioni, embedding di iterazione), tutti con runtime e tokenizer contati, a budget di 0.5,
1.0 e 1.44 MB. E1 addestra a parità esatta di byte tre varianti procedurali: (a) PRANC/Kilobyte a blocchi
con seed LFSR per blocco e coefficienti a 4 bit, (b) matrici casuali da seed + LoRA per profondità (#1113
ridotto), (c) ricorsivo + base casuale condivisa. Il criterio di uccisione F1 è: se nessuna variante
procedurale batte il migliore fra denso e ricorsivo in bpb di validazione a 1.44 MB con ≥3 seed, la tesi
dei pesi procedurali cade e resta solo la condivisione dei pesi. Il costo di espansione va misurato
subito (tempo di boot su CPU di riferimento, RAM di picco), perché è il punto su cui Parameter Golf ha
visto fallire tutte le varianti con generatore. E2 aggiunge poi la codifica entropica e la loss di rate a
tutti i bracci. Solo se E1/E2 danno un margine ha senso scalare i parametri effettivi (E3) e produrre
l'immagine FAT12 (E4).
