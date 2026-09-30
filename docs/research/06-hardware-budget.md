# Survey 6 — Budget hardware del laptop

Consolidato da ricerca web del 2026-09-30.

## Domanda

Cosa si allena e cosa si espande in tempo utile su questo laptop (i7-1165G7, 32 GB, no CUDA),
e quando servirebbe una GPU a noleggio?

## Cosa esiste

### Macchina (ispezione read-only)

- `lscpu`: i7-1165G7 Tiger Lake, 4C/8T, 0.4–4.7 GHz, L2 5 MiB, L3 12 MiB. AVX2, **AVX-512F/BW/VL,
  AVX512-VNNI** (int8 veloce), `avx512_bf16`/AMX **assenti** (bf16 emulato, lento).
- `free -h`: 31 GiB RAM (24 GiB available al momento), 47 GiB swap.
- torch 2.11.0 (build cu130, usata su CPU), `torch.get_num_threads()` = 4, oneDNN disponibile.
- Picco teorico stimato: 4 core × 32 FLOP/ciclo fp32 (una porta FMA-512 su Tiger Lake client) ×
  ~4 GHz ≈ 0.4–0.5 TFLOPS; TDP 28 W e governor termico abbassano il sostenuto.

### Micro-benchmark misurati (burst ≤5 s, turbo, script in scratchpad)

| Misura                                            |                                       Risultato |
| ------------------------------------------------- | ----------------------------------------------: |
| GEMM fp32 512² / 1024² / 2048²                    |                       92 / **117** / 116 GFLOPS |
| GEMM bf16 1024² / 2048²                           | 40 / 29 GFLOPS (niente bf16 nativo: usare fp32) |
| matvec fp32 4096×1024 (in cache L2/L3)            |                                         28 GB/s |
| matvec fp32 8192×8192 (256 MB, DRAM)              |                           **23 GB/s** effettivi |
| `torch.rand`/`randn` 100M fp32                    |                                           1.1 s |
| `torch.randint` int8 100M                         |                                           0.9 s |
| xorshift32 ×4 lane, C `-O3`, 1 thread, 100M float |                              0.37 s (1.08 GB/s) |
| PCG32, C, 1 thread, 100M float                    |                              0.39 s (1.03 GB/s) |
| LFSR16 Galois, 1 thread                           |                                   245 M passi/s |

Training di un decoder transformer (torch `TransformerEncoderLayer` causale, pre-norm, vocab
4096, T=256, B=16, AdamW, fp32, 4 thread):

| d / L   | Parametri (non-emb) | tok/s train | FLOPS effettivi (6N) | Token in 8 h |
| ------- | ------------------: | ----------: | -------------------: | -----------: |
| 256 / 4 |         5.3M (3.2M) |       3 016 |                ~95 G |     **~87M** |
| 384 / 6 |       13.8M (10.7M) |         986 |                ~82 G |         ~28M |
| 512 / 8 |       29.4M (25.2M) |         271 |                ~48 G |          ~8M |

Inferenza decode-like (catena di matvec fp32, batch 1, un token):

| Modello                  |   tok/s |
| ------------------------ | ------: |
| 30M (d=512, 9 blocchi)   | **113** |
| 100M (d=768, 14 blocchi) |  **31** |

- Coerente col limite di banda: 100M × 4 B = 400 MB/token → a 23 GB/s ≈ 57 tok/s teorici.
  int8 (VNNI) dimezza i byte: stima ~50–60 tok/s a 100M. Il target ≥5 tok/s ha margine 6×.
- I burst sovrastimano il sostenuto: sotto `bg` + governor attendersi −20/−40% nelle ore.

### Riferimenti esterni

- TinyStories: ~470M token train con tokenizer GPT-2
  ([conteggio 471.6M](https://arxiv.org/pdf/2405.17767)); con vocab 4096 (llama2.c `tok4096`)
  il conteggio sale (pezzi più corti), ordine 0.5–0.6B token.
- [llama2.c](https://github.com/karpathy/llama2.c): stories15M/42M/110M allenati su GPU (A100),
  non su CPU; run.c raggiunge centinaia di tok/s su stories15M su CPU desktop.
- GPU a noleggio settembre 2026: RTX 4090 ~$0.34–0.69/h (RunPod community/secure), ~$0.47/h
  Vast.ai; H100 ~$2–3/h ([Spheron](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-runpod-vs-vastai-2026/),
  [RunPod](https://www.runpod.io/pricing), [gpuperhour](https://gpuperhour.com/)); RTX 5090
  spot da ~$0.25/h ([TechRadar](https://www.techradar.com/pro/security/you-can-now-rent-a-usd3000-nvidia-rtx-5090-gpu-from-just-usd0-25-hour-when-you-need-it-for-as-long-as-you-need-it)).

## Cosa manca

- Benchmark di training su **parametrizzazione procedurale**: nessun numero pubblico su CPU. Il
  costo dominante è la forward/backward **effettiva** (30–100M), più la generazione dei pesi a
  ogni step (PRNG + combinazione lineare: ~P·N FMA per P basi per blocco, trascurabile se P≤8,
  oppure rigenerazione cacheata: le basi sono fisse, si allenano solo i coefficienti).
  Stima: tok/s procedurale ≈ tok/s denso a pari parametri effettivi × 0.6–0.9.
- Sostenuto notturno reale sotto governor termico: non misurato (serve un run `bg` di 30 min).
- Qualità attesa per token visti: i modelli TinyStories coerenti (1–33M) sono allenati su
  centinaia di M–miliardi di token; nessun dato su "30M effettivi con 8M token".

## Implicazione per FloppyLM

**Cosa si allena su CPU in una notte (8 h, sostenuto ~0.7× dei burst):**

- Denso 1–5M: ~60–90M token/notte (~15% di un'epoca TinyStories). Rapporto Chinchilla ~20
  token/param → 5M param saturano in ~1–2 notti. **E0 fattibile su CPU.** La frontiera densa a
  ~11 Mbit (survey 04) cade proprio qui: 11 Mbit / 4 bit ≈ 2.8M param, / 2 bit ≈ 5.6M.
- Denso/procedurale 10–15M effettivi: ~20M token/notte. Utile per smoke e ranking relativo,
  sotto-allenato in assoluto.
- Procedurale 30M effettivi: ~5–8M token/notte; 100M effettivi (d=768): stimati ~50–80 tok/s →
  **~1.5–2M token/notte**. Due ordini di grandezza sotto il necessario.

**Espansione al boot (F3):**

- PRNG: 100M pesi fp32 in ~0.4 s (1 thread) / ~0.1 s (4 thread). Con Philox/torch ~1 s.
- Ricombinazione basi×coefficienti (SeedLM-like, P=4–8): <1 GFLOP → <0.1 s.
- Generatore neurale (hypernetwork MLP, h=256 per peso): ~2·h·N ≈ 51 GFLOP → ~0.5–1 s.
- RAM: 100M fp32 = 400 MB (+KV cache pochi MB a T=256): dentro 1 GB; 100M int8 = 100 MB.
- **F3 non scatta** salvo generatori con >~50 kFLOP/peso (60 s × ~100 GFLOPS / 1e8 pesi).
- Generazione: 31 tok/s (100M fp32) / 113 tok/s (30M) misurati ≫ 5 tok/s.

**Quando servirebbe una GPU (non deciso qui):** training procedurale a 30–100M effettivi per
≥0.3–1B token. Conto: 6 × 1e8 × 1e9 ≈ 6e17 FLOP; RTX 4090 a ~40 TFLOPS utili bf16 → ~4 h ≈
**$2–3/run**; ×2–3 per overhead procedurale; una sweep di E3 (3 scale × 3 seed × 2 bracci)
≈ **$30–150**; su H100 stesso ordine di costo, meno ore. Su CPU la stessa run richiederebbe
~6e17 / 5e10 ≈ 140 giorni.

- **F4** (coerenza TinyStories) non è valutabile onestamente a 100M effettivi su CPU: il
  modello sarebbe sotto-allenato di 100×, e un fallimento F4 sarebbe confuso con mancanza di
  compute. Questo va dichiarato prima di E3.
- **F1** si può falsificare su CPU a piccola scala (E1 a 5–15M effettivi): se il procedurale
  non batte il denso lì, non c'è ragione di pagare la GPU.

## Esperimento minimo

- **E0** (CPU, fattibile): frontiera densa 0.5–5M param, quantizzata 2/3/4/8 bit, bit-accounting
  completo; ~1 notte per punto, 6–8 punti → 1–2 settimane di notti `bg`.
- **E1** (CPU, fattibile a scala ridotta): procedurale a pari `model_bytes`, 5–15M effettivi,
  stesso budget di token del denso (es. 60M). Decide F1 prima di spendere.
- **E2** (CPU, economico): rANS + rate loss applicati a entrambi i bracci; costo trascurabile
  rispetto al training (pochi minuti di encode/decode).
- **E3** (ibrido): misura del costo di boot 30–100M su CPU (secondi); scaling della qualità a
  30–100M effettivi → **GPU a noleggio** se E1 passa; su CPU solo curve troncate a ≤15M.
- **E4** (CPU): immagine FAT12 reale + boot da host pulito, misura end-to-end tempo di
  espansione e tok/s.
- Prima di E0: run `bg` di 30 min a d=256 per fissare il fattore sostenuto/burst reale.
