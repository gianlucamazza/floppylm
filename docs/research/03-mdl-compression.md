# Survey 3 — MDL, codifica dei pesi e prezzo in bit di un LM

Consolidato da ricerca web del 2026-09-30.

## Domanda

Quanto costa in bit un LM, contando modello e decompressore, e l'addestramento rate-aware (NLL + λ·bit
dei pesi, con codifica entropica) sposta la frontiera bpb-per-byte rispetto a quantizzare e comprimere a
valle?

## Cosa esiste

**Quadro MDL.** Hinton & van Camp (COLT 1993,
[doi:10.1145/168304.168306](https://doi.org/10.1145/168304.168306)) formulano l'addestramento come
minimizzazione della lunghezza di descrizione di pesi più errori, con pesi rumorosi il cui costo è una KL
(bits-back). Blier & Ollivier ([arXiv:1802.07044](https://arxiv.org/abs/1802.07044), NeurIPS 2018)
misurano davvero queste code-length: il codice variazionale è "sorprendentemente scarso" (MNIST 24.1
kbit, CIFAR-10 89.0 kbit per le etichette, modello incluso), mentre il codice prequenziale (addestrare
online e codificare ogni blocco con il modello corrente) scende a 4.10 kbit e 45.3 kbit, cioè 6× e 2×
meglio. Il limite, decisivo per noi, è che il codice prequenziale non trasmette i pesi: il ricevente li
riaddestra sui dati che sta decodificando. Per un artefatto che deve generare testo senza dati resta
applicabile solo il codice a due parti (pesi + NLL), cioè proprio il regime in cui le reti profonde
comprimono peggio. MIRACLE ([arXiv:1810.00440](https://arxiv.org/abs/1810.00440)) rende pratico il
bits-back con codifica a campione casuale: LeNet-5 in 1.52 KB (1110×, errore 0.96%) e VGG-16 CIFAR in 135
KB (452×).

**Codifica entropica addestrata.** Deep Compression
([arXiv:1510.00149](https://arxiv.org/abs/1510.00149)) mostra che pruning + quantizzazione a cluster +
Huffman dà 35–49× (AlexNet 240→6.9 MB, VGG-16 552→11.3 MB); su LeNet la sola quantizzazione dà ~32× e
Huffman porta a ~40×. Oktay et al. ([arXiv:1906.06624](https://arxiv.org/abs/1906.06624), ICLR 2020) sono
il riferimento metodologico diretto per la "loss rate-aware": parametri in uno spazio latente con modello
di probabilità appreso, penalità di entropia durante il training e codifica aritmetica alla fine, in un
solo stadio. Ottengono LeNet-5 in 2.84 KB (606×) e ResNet-18 ImageNet in 1.97 MB (24×) a parità di
errore, confrontandosi con Bayesian Compression e DeepCABAC. Self-Compressing Neural Networks
([arXiv:2301.13142](https://arxiv.org/abs/2301.13142)) apprendono la profondità di bit per canale con una
penalità sulla dimensione e mantengono accuratezza float con il 3% dei bit e il 18% dei pesi. Sul fronte
LLM recente la codifica entropica è quasi sempre post-training. Neural Weight Compression
([arXiv:2510.11234](https://arxiv.org/abs/2510.11234)) usa trasformate apprese e quantizzazione vincolata
in entropia, forte a 4–6 bit; EntroPack ([arXiv:2609.34185](https://arxiv.org/abs/2609.34185)) usa
reticolo E8 con modello condizionale a bitrate arbitrario (−24% errore L2 rispetto a NF4 a 4 bit);
[arXiv:2606.15789](https://arxiv.org/abs/2606.15789) misura un'entropia effettiva 2–10× sotto la
larghezza di bit nominale su LLM da 1.5B a 405B e la raggiunge con rANS entro 0.01–0.1 bit dal limite di
Shannon.

**Modello contato nel punteggio: LM come compressore.** Delétang et al.
([arXiv:2309.10668](https://arxiv.org/abs/2309.10668), ICLR 2024) mostrano che Chinchilla 70B comprime
enwik9 all'8.3% (≈0.66 bpb) se il modello è gratis, ma al 14 008% se i parametri si contano a 2 byte
l'uno. Per ogni dataset esiste una taglia critica oltre la quale il tasso "aggiustato" peggiora, e la
taglia ottima dipende dalla dimensione del testo da comprimere. Questo è il cuore della domanda FloppyLM:
con 11.8 Mbit a disposizione il termine "bit del modello" domina. Il Large Text Compression Benchmark
([LTCB](https://www.mattmahoney.net/dc/text.html)) e l'Hutter Prize
([prize.hutter1.net](http://prize.hutter1.net/), dove conta la somma compressore + archivio
autoestraente) danno numeri concreti. Il record accettato è fx2-cmix (Orav & Knoll, settembre 2024), 110
793 128 byte totali su enwik9, ≈0.886 bpb. Fra le iscrizioni 2026 in verifica, fx2-cmix-transformer
(Ivanov, luglio 2026) sostituisce l'LSTM online con un Transformer da 6M parametri preaddestrato offline
(8 RTX 5090 per 26 h), quantizzato a 4 bit pesi / 8 bit attivazioni, che aggiunge 2.9 MB al binario:
archivio 96 996 198 + compressore 3 428 474 byte, ≈0.803 bpb. zmix (settembre 2026) e
cmix-lex-transformer lexth11c (27 settembre 2026, 95 836 613 + 3 477 137 = 99 313 750 byte, ≈0.795 bpb)
riaddestrano quei pesi "ottimizzati per la quantizzazione". È la prima volta che nel Prize vince un
modello a due parti con pesi preaddestrati memorizzati invece di uno puramente online. NNCP (Bellard,
[bellard.org/nncp](https://bellard.org/nncp/); v3.2 nel LTCB, v3.3 corrente) resta prequenziale:
Transformer addestrato durante la (de)compressione, decompressore di 628 955 byte, enwik8 14 915 298 byte
(≈1.193 bpb) ed enwik9 106 632 363 byte (≈0.853 bpb). cmix v21 fa enwik8 in 14 623 723 byte (≈1.170 bpb).

**Budget di byte fisso per un LM generativo: Parameter Golf.** La sfida OpenAI
([repo](https://github.com/openai/parameter-golf), [arXiv:2607.01517](https://arxiv.org/abs/2607.01517))
misura bpb su FineWeb con artefatto (codice + pesi compressi) ≤16 MB. Su 2 037 PR la frontiera scende da
1.2244 (int8 + zlib, 9 layer × 512) a 1.058, e l'analisi dei contributi indica come scelta affidabile
int6 con QAT-STE (libera ~4 MB), più GPTQ e Brotli. Il ternario risulta neutro e il binario negativo: "i
formati a bit molto bassi cedono più di quanto il budget liberato possa recuperare". Punti concreti:
ternario 73.7M parametri 1.157 bpb nel track da 10 minuti; binario 106M parametri con 2 h di training
1.1239; BitNet 68M ternari impacchettati a 1.6 bit/param in 15.88 MB 1.177
([#367](https://github.com/openai/parameter-golf/pull/367)). Sul ternario, quella PR riporta che quasi
tutto lo stack standard (weight decay, XSA, SWA) "rompe o non aiuta". Il QAT con regolarizzazione di
entropia verso la griglia dimezza il gap di quantizzazione da 0.017 a 0.009 bpb
([#885](https://github.com/openai/parameter-golf/pull/885)); una penalità di entropia sui pesi migliora
la media SWA di 0.028 bpb ([#459](https://github.com/openai/parameter-golf/pull/459)); una PR di QAT
regolarizzato in entropia sui simboli quantizzati è rimasta WIP
([#930](https://github.com/openai/parameter-golf/pull/930)). La leaderboard mostra anche un rischio
metodologico: cache n-gram e test-time training in valutazione hanno prodotto "record" a 0.08–0.4 bpb,
quindi il protocollo di valutazione va fissato prima di confrontare numeri.

**Il ternario e il basso bit come punto di rate.** BitNet b1.58
([arXiv:2402.17764](https://arxiv.org/abs/2402.17764)) addestra da zero con pesi {−1,0,1} e dichiara
parità di perplexity con FP16 a pari taglia e token (nel paper, dai ~3B parametri). Spectra/TriLM
([arXiv:2407.12327](https://arxiv.org/abs/2407.12327)) trova che i ternari superano float e quantizzati a
parità di bit solo sopra ~1B parametri: il TriLM da 3.9B pareggia il FloatLM da 3.9B con meno bit del
FloatLM da 830M. ParetoQ ([arXiv:2502.02631](https://arxiv.org/abs/2502.02631), NeurIPS 2025) unifica il
QAT sotto i 4 bit: ternario, 2 e 3 bit sono comparabili nel trade-off taglia/accuratezza e in genere
battono 4 bit e binario, con una transizione di apprendimento fra 2 e 3 bit. Scaling Laws for Precision
([arXiv:2411.04330](https://arxiv.org/abs/2411.04330)) modella la bassa precisione come riduzione dei
parametri effettivi e mostra che il degrado da quantizzazione post-training cresce con i token di
preaddestramento, cosa che favorisce il QAT dall'inizio per modelli molto addestrati. BITCOS
([arXiv:2609.16338](https://arxiv.org/abs/2609.16338)) misura fino al 51.5% di zeri in 29 LLM ternari e
li memorizza a 1.485 bit/peso, sotto il log₂3 = 1.585 nominale: il ternario non è un punto di rate fisso,
e la sparsità lo rende codificabile entropicamente.

**Ordini di grandezza per il floppy.** 1 474 560 byte sono 11.80 Mbit. Tolti ~50–100 KB di runtime e
tokenizer, restano circa 2.7–2.9M parametri a 4 bit, ~7.0–7.3M ternari impacchettati a 1.6 bit, oppure
~8–9M ternari codificati entropicamente a ~1.3 bit se la sparsità è alta come in BITCOS. Su scala
TinyStories ([arXiv:2305.07759](https://arxiv.org/abs/2305.07759)) i modelli da 1–3M generano già testo
scorrevole ma poco coerente, mentre la coerenza narrativa emerge verso 10–30M. Il salto che la tesi
FloppyLM deve comprare con la descrizione procedurale è quindi di circa un ordine di grandezza di
parametri effettivi. Come documenta la Survey 1, quei conteggi escludono la tabella di embedding (vocab
50 257, ~3.2M parametri nel solo 1M), quindi il vocabolario va ridotto e contato nel budget.

## Cosa manca

Ho cercato "entropy-penalized training language model from scratch", "rate-distortion transformer weights
training", "compressible transformer arithmetic coding bits per parameter" e, dentro Parameter Golf, PR
su entropy regularization, compressibility, Brotli, ternary e BitNet. Non ho trovato nessun LM addestrato
da zero con loss esplicita NLL + λ·(bit codificati dei pesi), in stile Oktay 2020, valutato in bpb per
byte totali di artefatto. Oktay, MIRACLE e Self-Compressing sono validati su CNN di visione. I metodi
entropici per LLM (NWC, EntroPack, BITCOS, rANS) sono post-training. In Parameter Golf l'entropia compare
solo come regolarizzatore ausiliario del QAT (#885, #459) e il tentativo esplicito (#930) non ha
risultati. Manca anche la frontiera sotto 2 MB: Parameter Golf vive a 16 MB, l'Hutter Prize a ~100 MB con
un modello da 2.9 MB che però lavora dentro un mixer di contesto (non è un LM generativo autonomo), e i
punti TinyStories sotto il MB (stories260K, Single Floppy 346K) sono densi FP32 senza alcuna codifica. Il
pezzo mancante è la curva bpb vs byte totali tra 0.3 e 1.5 MB, con QAT a 2–4 bit, ternario, codifica
entropica e loss di rate applicati in modo uniforme. Non esiste nemmeno la misura di quanto la loss di
rate aggiunga rispetto a "QAT + Brotli/rANS a valle", che in Parameter Golf è già forte.

## Implicazione per FloppyLM

**F2** è la condizione più esposta. La letteratura dice che codifica entropica e basso bit con QAT,
applicati al denso, sono già molto efficaci (Deep Compression +25% da Huffman; BITCOS sotto 1.585 bit;
int6 QAT + Brotli dominante in Parameter Golf). Qualunque vantaggio procedurale va quindi misurato contro
un denso che riceve la stessa codifica, altrimenti è un artefatto della baseline. La loss di rate è un
metodo applicabile a tutti i bracci, non un vantaggio proprio dei pesi procedurali. **F1**: il ternario è
poco competitivo sotto 1B (Spectra) e neutro a 16 MB (Parameter Golf), mentre ParetoQ indica 2–3 bit come
ottimo. La baseline densa corretta per il floppy è quindi QAT a 2–3 bit o ternario con codifica
entropica, non int4 ingenuo, e questo alza l'asticella per i procedurali. **F4**: 2.8–9M parametri
effettivi densi sono a cavallo della soglia di coerenza TinyStories, quindi F4 non è scontato nemmeno per
il denso ed è lì che un modello effettivo più grande dovrebbe pagare. Il codice prequenziale (NNCP, Blier
& Ollivier) suggerisce infine un controllo che la tesi non considera: "descrizione = corpus compresso +
trainer", con addestramento al boot. È quasi certamente peggiore (1.4 MB compressi sono pochi milioni di
token) e viola F3, ma delimita il limite MDL dal basso e costa poco.

## Esperimento minimo

E0 fissa il protocollo: bpb su validazione TinyStories senza cache né TTT in valutazione, byte contati
dall'immagine finale (pesi codificati + tabelle di probabilità + tokenizer + runtime), almeno 3 seed. Poi
misura la frontiera densa a 0.5 / 1.0 / 1.44 MB per int4, 3 bit, 2 bit e ternario in QAT, ciascuno con
Brotli/zstd a valle e con rANS su simboli quantizzati. E2 aggiunge a ogni braccio, denso, ricorsivo e
procedurale, la stessa loss di rate (entropia dei simboli quantizzati sotto un prior fattorizzato
appreso, alla Oktay; λ in sweep) e registra lo spostamento della frontiera. La domanda della survey ha
risposta se, a byte uguali, "rate loss + rANS" batte "QAT + Brotli" di un margine superiore alla varianza
fra seed. F2 scatta se il vantaggio procedurale di E1 scompare quando anche il denso riceve rate loss +
codifica entropica + pruning. Il controllo prequenziale (corpus compresso + trainer) va in E2 come riga
singola della tabella, con tempo di boot annotato per E3.
