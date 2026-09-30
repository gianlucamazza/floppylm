# Survey 5 — Valutare modelli minuscoli a parità di byte senza poter barare

Consolidato da ricerca web del 2026-09-30.

## Domanda

Come si confrontano modelli minuscoli a parità di byte su disco, in modo che il confronto tra un modello
procedurale e la frontiera densa non si possa truccare né con il tokenizer, né con i dati, né con
l'accounting?

## Cosa esiste

**Bits-per-byte contro perplessità.** La perplessità per token non è confrontabile tra tokenizer
diversi: un vocabolario più grosso fa token più lunghi e cambia la loss per token anche a parità di
capacità predittiva. The Pile (Gao et al. 2020, [arXiv:2101.00027](https://arxiv.org/abs/2101.00027))
ha codificato come metrica preferita i bit per byte UTF-8, BPB = (L_T/L_B)·ℓ/ln 2, dove ℓ è la loss media
in nat per token, L_T i token e L_B i byte UTF-8 del testo valutato, motivandola con l'invarianza al
tokenizer e con l'ambiguità del "carattere" in Unicode (per GPT-2 su Pile, L_T/L_B ≈ 0.293). Per noi
questo è indispensabile: i candidati avranno vocabolari da 256 (byte-level) a 2048 token e un modello
procedurale potrebbe usare un tokenizer ancora diverso. Il BPB va calcolato sul testo originale e il
tokenizer deve fare round-trip esatto byte→token→byte; un tokenizer che normalizza (minuscole, spazi,
caratteri rari scartati) abbassa artificialmente la loss e va squalificato o penalizzato contando i byte
persi.

**Compressione come misura.** Delétang et al., "Language Modeling Is Compression" (ICLR 2024,
[arXiv:2309.10668](https://arxiv.org/abs/2309.10668)), rendono esplicita l'equivalenza
predizione↔compressione lossless (Chinchilla 70B comprime patch ImageNet al 43.4% e LibriSpeech al 16.4%,
meglio di PNG e FLAC) e, soprattutto, introducono un tasso di compressione _aggiustato_ che somma la
dimensione del modello in byte: con questo accounting esiste per ogni dataset una dimensione critica oltre
la quale i parametri pesano più di quanto facciano risparmiare, e "la dimensione del dataset impone un
limite duro alla dimensione del modello". Huang et al., "Compression Represents Intelligence Linearly"
(COLM 2024, [arXiv:2404.09937](https://arxiv.org/abs/2404.09937)), su 31 LLM pubblici e 12 benchmark
trovano una correlazione di Pearson di circa −0.93 tra bit per carattere su corpora esterni e punteggio
medio a valle (−0.94/−0.95 per conoscenza, codice, matematica). Due scelte metodologiche sono da copiare:
corpora di valutazione raccolti dopo il cutoff di tutti i modelli (Common Crawl, GitHub, arXiv di
settembre–ottobre 2023) per evitare contaminazione, e una finestra di contesto unica (1900 token) per
tutti perché un contesto più lungo favorisce la compressione. Il caveat dichiarato è che il risultato vale
per base model ben addestrati e in regime di contesto breve-medio; nessuno lo ha verificato sotto i 10M.

**Hutter Prize e LTCB: il decompressore conta.** L'Hutter Prize ([Wikipedia](https://en.wikipedia.org/wiki/Hutter_Prize),
[regole](http://prize.hutter1.net/hrules.htm)) misura enwik9 (10⁹ byte di Wikipedia) come dimensione
dell'archivio _più_ dimensione dell'eseguibile decompressore; il record corrente è fx2-cmix di Orav e Knoll,
110 793 128 byte (settembre 2024), con vincoli di esecuzione (≲50 ore su un core, <10 GB RAM, niente GPU) e
divieto di qualunque informazione esterna al momento della decompressione (rete, corpora installati, dati
del sistema operativo). Il Large Text Compression Benchmark di Mahoney
([textrules](https://www.mattmahoney.net/dc/textrules.html)) conta il file compresso più lo zip del
decompressore con dizionari, file di configurazione e librerie non standard, scegliendo il minore tra
eseguibile e sorgente. È esattamente la regola che serve a FloppyLM: il generatore procedurale, le tabelle
e il runtime _sono_ parte del modello, e un'informazione presa dal sistema ospite è un furto di bit.

**TinyStories e il giudice GPT.** Eldan & Li ([arXiv:2305.07759](https://arxiv.org/abs/2305.07759))
valutano la generazione chiedendo a GPT-4 di correggere il completamento "come un insegnante",
con voti su 10 per grammatica, creatività, coerenza con l'inizio (e trama/aderenza alle istruzioni nella
variante Instruct), su prompt scritti a mano fuori dal training set. SimpleStories
([arXiv:2504.09184](https://arxiv.org/abs/2504.09184)) ripete lo schema con GPT-4o-mini, chain-of-thought,
scala 0–100 e N=200 campioni. Il giudice LLM è però manipolabile: Wang et al., "Large Language Models are
not Fair Evaluators" ([arXiv:2305.17926](https://arxiv.org/abs/2305.17926)), mostrano che invertendo
l'ordine di presentazione Vicuna-13B batte ChatGPT su 66 query su 80 con ChatGPT come giudice, e
propongono calibrazione con evidenze, bilanciamento delle posizioni e revisione umana dei casi a entropia
alta. Il giudice va quindi fissato per versione, usato in valutazione assoluta per singolo campione e
ancorato a un modello di riferimento valutato nella stessa sessione.

**BLiMP e la pipeline BabyLM.** BLiMP (Warstadt et al., TACL 2020,
[ACL](https://aclanthology.org/2020.tacl-1.25/)) contiene 67 paradigmi da 1000 coppie minime generate da
grammatiche, con accordo umano del 96.4%; il modello "passa" una coppia se assegna probabilità più alta
alla frase accettabile, quindi la metrica è puramente probabilistica e indipendente dal campionamento.
La pipeline BabyLM 2025 ([github.com/babylm/evaluation-pipeline-2025](https://github.com/babylm/evaluation-pipeline-2025),
[findings](https://aclanthology.org/2025.babylm-main.28/)) per i track strict e strict-small usa BLiMP,
BLiMP supplement, EWoK, COMPS, entity tracking (riformulato come scelta della continuazione più probabile)
e Global PIQA inglese, con checkpoint intermedi e budget di compute. Il limite per noi è che BLiMP usa
lessico adulto fuori dal dominio TinyStories: un modello da 2–7M addestrato su storie per bambini sarà
vicino al caso su molti paradigmi per ragioni di vocabolario, non di sintassi. Va usato solo come
diagnostica secondaria, su un sottoinsieme filtrato per vocabolario del corpus.

**Split e contaminazione.** Il dataset TinyStories è contaminato: secondo Pearce et al.
([arXiv:2406.03947](https://arxiv.org/abs/2406.03947), App. C.3) ~15% dei campioni di training sono
duplicati e ~30% del validation set compare nel training; gli autori uniscono train e validation,
eliminano i duplicati esatti, rimescolano e ri-splittano. Qualunque bpb calcolato sul validation ufficiale
premia la memorizzazione, e premia di più proprio i modelli con più parametri effettivi, cioè il
procedurale espanso: un bias che gonfierebbe F1 a favore della tesi.

**Il baseline deve essere buono.** "Baseline Shape Decides the Verdict" (2026,
[arXiv:2609.29397](https://arxiv.org/abs/2609.29397)) mostra che a budget di byte fisso transformer con lo
stesso numero di parametri differiscono del 22.6% in validation loss solo per forma, che un confronto
precedente lasciava gli embedding posizionali in piena precisione (11–22% dei parametri) al baseline
rendendolo "meno quantizzato", e che il vantaggio di un regime di training cambia segno col learning rate.
È il catalogo dei modi in cui un confronto a pari byte si trucca involontariamente.

## Cosa manca

Non esiste un protocollo pubblicato che unisca bpb held-out, accounting "tutto ciò che serve a generare
sta nel budget" alla Hutter e una soglia di coerenza generativa per modelli sotto i 10M. Abbiamo cercato
controesempi al piano di usare il bpb come metrica primaria: evidenze che a scala minuscola bpb e
coerenza giudicata divergano (TinyStories mostra invece che tutti i voti GPT-4 salgono al calare della
loss, con la grammatica che satura prima), e studi che validino la correlazione di Huang sotto i 100M
(nessuno trovato). Abbiamo cercato anche bpb pubblici per i checkpoint TinyStories/llama2.c (solo loss
per-token con tokenizer diversi, non confrontabili) e una valutazione del giudice GPT-4 contro voti umani
su storie per bambini (solo evidenze generiche di inflazione e bias di posizione). Manca infine una
convenzione su cosa sia "sistema ospite" ammesso: kernel e libc sì, ma Python, PyTorch o BLAS di sistema
renderebbero il runtime gratis, e nessuna fonte lo regola per i modelli locali.

## Implicazione per FloppyLM

La metrica primaria è il bpb held-out calcolato _dall'artefatto_, non dal checkpoint PyTorch: il runtime
sull'immagine produce le log-probabilità che il harness somma, così qualunque discrepanza tra modello
dichiarato e modello espanso emerge. Il set proposto è questo. **(M1) bpb** = Σ NLL in bit / byte UTF-8 su
uno split di test ricavato da TinyStories deduplicato (esatto e near-duplicate su 13-gram) e ri-splittato
per hash del testo, più un secondo test out-of-distribution di storie generate dopo la fine del training
con lo stesso lessico; contesto fisso (512 byte-equivalenti) con finestra scorrevole, documenti interi,
stesso per tutti; tokenizer con round-trip byte-esatto verificato. **(M2) regola di accounting**:
B_total = somma dei cluster allocati sull'immagine FAT12 (≤1 457 664 byte utili su 1 474 560 grezzi),
comprendente eseguibile statico del runtime ed espansore, tokenizer, pesi/seed/coefficienti e ogni tabella;
ammessi dal sistema ospite solo kernel Linux x86-64, libc e CPU, niente rete, niente file esterni, niente
librerie numeriche; il confronto F1 è a B_total uguale entro 1%, riportato come curva bpb-vs-B_total, e
l'espansione deve essere deterministica (hash dei pesi espansi identico su 5 boot). **(M3) parità di
trattamento** per F2: stesso corpus, stessi token di training, stesso budget di ricerca iperparametri e di
forma, stessa pipeline di pruning e codifica entropica dei pesi applicata a ogni candidato. **(M4) costo
di boot** per F3: tempo di espansione dal mount a primo token ≤60 s, RSS di picco ≤1 GB, ≥5 tok/s
mediana su 5 run su i7-1165G7 a 4 thread con governor e stato termico dichiarati (la slice
background è throttlata dal governatore termico, quindi le misure vanno fatte fuori da essa). **(M5)
coerenza** per F4: 50 prompt di inizio storia held-out, 4 campioni ciascuno a temperatura 0.8/top-p 0.9,
giudice LLM a versione fissata in valutazione assoluta cieca con ordine randomizzato, voti di grammatica e
coerenza su 10; F4 scatta se il modello non raggiunge la non-inferiorità (margine 0.5 punti) rispetto a
`roneneldan/TinyStories-8M` valutato nella stessa sessione, oppure scende sotto il pavimento assoluto
grammatica ≥6 e coerenza ≥5, con un controllo umano cieco su 30 campioni e un tasso di 4-gram ripetuti
come allarme meccanico contro la degenerazione. BLiMP filtrato e l'entity tracking BabyLM sono diagnostica,
non criterio. Rispetto a F0, il protocollo stesso è una parte difendibile del contributo, perché nessuno
dei lavori affini (VBQ, SeedLM, Atome) riporta byte totali su supporto fisico insieme a bpb held-out pulito.

## Esperimento minimo

E0 congela il protocollo prima di qualunque modello procedurale: dedup e resplit di TinyStories, test OOD
generato e hashato, harness che invoca il runtime C e somma le log-prob, script di accounting che legge
l'immagine; poi misura la frontiera densa (int8, 4 bit, ternario, sweep di forma e vocabolario) e ne
pubblica la curva bpb-vs-byte e i voti M5 contro TinyStories-8M. E1 valuta il modello procedurale con lo
stesso harness a B_total uguale entro 1%, senza modificare nulla del protocollo dopo aver visto i
risultati. E2 applica a tutti la stessa codifica entropica e lo stesso pruning, eventualmente con rate loss
in training, e ricalcola le curve per testare F2. E3 scala i parametri effettivi espansi e misura M4 per
ogni punto, dichiarando dove F3 fallisce. E4 scrive l'immagine FAT12 reale, la monta su una macchina pulita
senza ambienti Python e ripete M1, M4 e M5 usando solo i file dell'immagine, confrontando i risultati con
quelli di E1–E3 per escludere che il modello valutato in laboratorio sia diverso da quello sul floppy.
