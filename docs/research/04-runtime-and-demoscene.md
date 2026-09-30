# Survey 4 — Runtime, packer e demoscene

Consolidato da ricerca web del 2026-09-30.

## Domanda

Quanti byte del floppy si mangia il runtime (binario + tokenizer + filesystem), e cosa insegna la
demoscene sul **generare invece di stoccare**?

## Cosa esiste

### Filesystem: quanto resta davvero su un 1.44 MB

Misurato in locale (`mkfs.fat -C -F 12 fd.img 1440`, `minfo`, `mdir`):

| Regione                            | Settori |          Byte |
| ---------------------------------- | ------: | ------------: |
| Boot sector                        |       1 |           512 |
| 2 × FAT12 (9 settori ciascuna)     |      18 |         9 216 |
| Root dir (224 entry × 32 B)        |      14 |         7 168 |
| **Overhead FAT12**                 |  **33** |    **16 896** |
| Area dati (2 847 cluster da 512 B) |   2 847 | **1 457 664** |

- Totale immagine 1 474 560 B; `mdir` riporta 1 457 664 byte liberi. Slack per file ≤511 B
  (cluster = 1 settore): con 3–4 file il costo è <2 KB.
- Un floppy "raw" (dd senza FS) darebbe tutti i 1 474 560 B, ma non è leggibile come floppy dati
  da un host qualsiasi: E4 deve usare FAT12. I formati 1.68 MB (DMF) / 1.722 MB (usati da
  [tomsrtbt](https://en.wikipedia.org/wiki/Tomsrtbt)) sono fuori contratto: il budget è 1 474 560.

### Runtime di inferenza: da 18 KB a 18 MB

Misurato in locale su [`llama2.c/run.c`](https://github.com/karpathy/llama2.c) (38 545 B di
sorgente, gcc 15, x86-64):

| Build                                                                      |    Byte |
| -------------------------------------------------------------------------- | ------: |
| `gcc -Os`, dinamico glibc, `strip -s`                                      |  18 848 |
| idem + `-ffunction-sections --gc-sections -fno-asynchronous-unwind-tables` |  18 840 |
| idem, `xz -9e` (solo come stima dell'entropia del codice)                  |   7 156 |
| `gcc -Os -static` glibc, strip                                             | 927 872 |
| idem `xz -9e`                                                              | 328 596 |

- glibc statico è inutilizzabile (~0.9 MB = 63% del floppy). musl statico: hello world ~7 KB
  vs ~600 KB glibc ([sta.li FAQ](https://sta.li/faq/),
  [Chainguard](https://edu.chainguard.dev/chainguard/chainguard-images/about/images-compiled-programs/glibc-vs-musl/));
  per run.c (solo libm + stdio + mmap) la stima è **30–60 KB** statico strippato. `musl-gcc` non
  è installato: numero da misurare in E4.
- llama.cpp: `llama-cli` locale è 1.06 MB, ma trascina `libllama` 3.6 MB + `libggml-base` 0.8 MB
  - `libllama-common` 4.9 MB (+ backend): **≥10 MB**. Escluso: 7× il floppy.
- Porte minime esistenti: [dosllam2](https://github.com/yeokm1/dosllam2) (llama2.c su DOS 32-bit),
  decine di port single-file (Java, Rust, Zig). tinygrad/runtime Python presuppongono un
  interprete sull'host: ammessi solo se ADR 0001 dichiara "host con Python" — sconsigliato,
  sposta byte fuori dal conteggio.
- Il runtime FloppyLM deve aggiungere a run.c: decoder entropico (rANS/range coder: 1–3 KB di
  codice; il depacker di kkrunchy è ~300 B in x86 a mano) + generatore PRNG (<1 KB) + la
  "ricetta" (base × coefficienti). Stima: **+3–6 KB** sul binario.

### Packer eseguibili: ratio tipici

- **UPX** (ELF/PE): 40–60% della dimensione originale, `--lzma`/`--ultra-brute` fino a ~30%
  ([upx(1)](https://man.archlinux.org/man/extra/upx/upx.1.en)). Su un binario da 20 KB il
  guadagno è ~10 KB: marginale, e non vale per i pesi (già entropy-coded).
- **kkrunchy** (farbrausch, 2006): LZ77 + arithmetic coding + modello x86 specifico; esempio
  riportato 41.5 KB (UPX) → 32.5 KB, cioè −22% rispetto a UPX
  ([ryg blog](https://fgiesen.wordpress.com/2011/01/24/x86-code-compression-in-kkrunchy/),
  [pouët](https://www.pouet.net/prod.php?which=26088)).
- **Crinkler** (4k/8k): linker-compressore context-mixing, de facto per 4k
  ([code4k](http://code4k.blogspot.com/2010/12/crinkler-secrets-4k-intro-executable.html)).
- **squishy** (Logicoma): successore di kkrunchy per 64k, comprime meglio a costo di molta CPU
  ([logicoma](https://logicoma.io/squishy/)).
- Lezione: i packer della scena guadagnano con **context mixing su codice**; sui pesi il lavoro
  equivalente è il nostro entropy coder (E2). Tutti sono Windows/PE; su Linux ELF resta UPX o un
  depacker xz/rANS fatto a mano.

### Demoscene: generare invece di stoccare

- **.kkrieger** (theprodukkt/farbrausch, Breakpoint 2004): FPS completo in 96 KB. Texture salvate
  come **storia di creazione** (grafo di operatori) invece che per-pixel; mesh da primitive
  deformate; audio sintetizzato. Solo storia + codice del generatore nell'eseguibile
  ([Wikipedia](https://en.wikipedia.org/wiki/.kkrieger),
  [sorgente werkkzeug3](https://github.com/jaromil/kkrieger-werkkzeug3)). Espansione in RAM di
  centinaia di MB a partire da ~96 KB: rapporto >1000×, pagato in tempo di caricamento.
- **4k/64k intro**: stesso principio — i dati sono un programma. Il rapporto funziona perché i
  contenuti (texture, musica) hanno **struttura generativa compatta** e tollerano perdita
  percettiva. Il costo nascosto: ore di authoring umano per trovare la ricetta.
- **Linux su floppy**: tomsrtbt (2002, 1.722 MB), [Floppinux 2025](https://krzysztofjankowski.com/floppinux/floppinux-2025.html):
  kernel 6.14 ~830 KB, restano **264 KB** liberi. Un floppy bootabile Linux lascia <20% al modello.
  FreeDOS kernel + shell ≈ 100 KB, più DOS extender per un binario 32-bit (dosllam2).

### PRNG per rigenerare pesi

| PRNG                                                                                                   | Stato       | Proprietà                                                                          | Throughput misurato (1 thread, i7-1165G7)                                     |
| ------------------------------------------------------------------------------------------------------ | ----------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| xorshift32 (×4 lane)                                                                                   | 4 B/lane    | seriale per lane, qualità bassa ma sufficiente per basi                            | 100M float in 0.37 s (1.08 GB/s scritti)                                      |
| PCG32                                                                                                  | 8 B         | seriale, buona qualità, jump-ahead O(log n)                                        | 100M float in 0.39 s (1.03 GB/s)                                              |
| LFSR 16 bit (SeedLM)                                                                                   | 2 B         | seed = 16 bit per blocco, hardware-friendly                                        | 245 M passi/s scalari; blocchi indipendenti → parallelo                       |
| Philox4x32-10 ([Random123](https://www.thesalmons.org/john/random123/releases/latest/docs/index.html)) | counter+key | **counter-based**: w[i] = f(key, i), accesso casuale, rigenerazione parallela/lazy | stesso ordine (è il default di torch su CUDA); `torch.rand` CPU 100M in 1.1 s |

- [SeedLM (Apple, ICLR 2025)](https://arxiv.org/abs/2410.10714): per ogni blocco di pesi un seed
  LFSR genera una matrice pseudo-casuale combinata linearmente con pochi coefficienti quantizzati;
  3–4 bit/peso, data-free, post-training su Llama. Dimostra che "seed + coefficienti" regge a
  scala LLM, ma **comprime un modello denso esistente** (≥ bit/peso), non espande.
- Per FloppyLM il PRNG non è il collo di bottiglia: 100M pesi fp32 = 400 MB generati in ~0.1 s
  su 4 core. Serve counter-based (Philox o LFSR per blocco) se si vuole rigenerare layer al volo
  invece di tenerli in RAM.

## Cosa manca

- Nessun LM "demoscene-style" documentato: cercati `kkrieger language model`, `64k intro neural
network`, `procedural weights floppy`; esistono solo reti minuscole in 4k/64k (sintesi,
  shader), non LM. Contro-esempio non trovato, ma la ricerca è per parole chiave (F0 resta a
  survey 02).
- Nessun numero misurato di run.c statico musl + decoder: stima 30–60 KB, da chiudere in E4.
- Il tokenizer non ha "packer" standard: misurato su vocabolario proxy (BERT, ordine
  frequenza): 512 voci 2.7 KB raw / 1.6 KB xz; 4096 voci 28 KB raw / **13 KB xz**; 8192 voci
  59 KB / 27 KB. Formato `tokenizer.bin` di llama2.c (score float + len) a 4096 voci: 57 KB —
  gli score sono ricavabili dal rango, vanno eliminati.

## Implicazione per FloppyLM

Conto dei byte (area dati FAT12 = 1 457 664 B):

| Scenario                                          |   Runtime |        Tokenizer | Slack/meta |      **Resta al modello** |
| ------------------------------------------------- | --------: | ---------------: | ---------: | ------------------------: |
| Floppy dati, host Linux, run.c dinamico + decoder |    ~24 KB | 13 KB (4096, xz) |      ~2 KB | **~1 418 KB ≈ 11.3 Mbit** |
| Floppy dati, musl statico + decoder (portabile)   |    ~60 KB |            13 KB |      ~2 KB | **~1 382 KB ≈ 11.0 Mbit** |
| Conservativo: statico, tokenizer llama2.c raw     |    ~65 KB |            57 KB |      ~2 KB |     ~1 334 KB ≈ 10.7 Mbit |
| Bootabile Linux (Floppinux)                       | ~1 190 KB |                — |          — |       ≤264 KB: tesi morta |

- **Runtime + tokenizer + FS realistico ≈ 40–90 KB (3–6% del floppy)**. Il modello dispone di
  **~1.38–1.42 MB ≈ 11 Mbit**. Il runtime non è il problema: lo è il rapporto bit/parametro.
- ADR 0001 deve fissare: floppy **dati** letto da host x86-64 Linux, binario statico musl (no
  dipendenze non contate), `image_bytes` = 1 474 560. Bootabile = fuori scope.
- **F0**: demoscene e SeedLM sono prior art del principio, non del prodotto (SeedLM comprime,
  non allena in regime generativo). Non chiude F0.
- **F1/F2**: la lezione .kkrieger è che la generazione batte lo stoccaggio solo se il contenuto
  ha struttura compatta. Pesi di LM sono vicini al rumore: senza entropy coding identico sul
  baseline denso (F2), qualunque vantaggio procedurale è sospetto.
- **F3**: la rigenerazione PRNG costa <1 s per 100M pesi: F3 non scatta per il PRNG; scatta
  solo se il generatore è una rete pesante (vedi survey 06).

## Esperimento minimo

- **E0**: harness di bit-accounting che stampa `runtime_bytes` misurando il binario reale
  (musl statico `-Os`, strip, con e senza UPX) e `tokenizer_bytes` per vocab 512/1024/4096
  compressi; fissa il `model_bytes` disponibile per la frontiera densa.
- **E1**: il budget procedurale usa lo stesso `model_bytes`; seed e coefficienti contati.
- **E2**: stesso entropy coder (rANS) per denso e procedurale; il codice del decoder conta una
  sola volta nel runtime.
- **E3**: misura il tempo di espansione con Philox/LFSR/xorshift a 30–100M; target ≤60 s,
  atteso <5 s.
- **E4**: immagine `mkfs.fat -C -F 12 fd.img 1440` + `mcopy`, verifica `mdir` e boot da host
  pulito (container senza toolchain) → `image_bytes` = 1 474 560 misurato, non stimato.
