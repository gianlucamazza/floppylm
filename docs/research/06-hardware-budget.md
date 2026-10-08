# Survey 6 — Laptop hardware budget

Consolidated from web research on 2026-09-30.

> **Framed for thesis v0.1.** Its "Minimum experiment" section predates [concept v0.2](../concept.md); E0–E4 are defined only by the [roadmap](../roadmap.md).

## Question

What can be trained and what can be expanded in useful time on this laptop (i7-1165G7, 32 GB, no CUDA),
and when would a rented GPU be needed?

## What exists

### Machine (read-only inspection)

- `lscpu`: i7-1165G7 Tiger Lake, 4C/8T, 0.4–4.7 GHz, L2 5 MiB, L3 12 MiB. AVX2, **AVX-512F/BW/VL,
  AVX512-VNNI** (fast int8), `avx512_bf16`/AMX **absent** (bf16 emulated, slow).
- `free -h`: 31 GiB RAM (24 GiB available at the time), 47 GiB swap.
- torch 2.11.0 (cu130 build, used on CPU), `torch.get_num_threads()` = 4, oneDNN available.
- Estimated theoretical peak: 4 cores × 32 FLOP/cycle fp32 (one FMA-512 port on client Tiger Lake) ×
  ~4 GHz ≈ 0.4–0.5 TFLOPS; the 28 W TDP and the thermal governor lower the sustained rate.

### Measured micro-benchmarks (bursts ≤5 s, turbo, script in scratchpad)

| Measurement                                        |                                    Result |
| -------------------------------------------------- | ----------------------------------------: |
| GEMM fp32 512² / 1024² / 2048²                     |                 92 / **117** / 116 GFLOPS |
| GEMM bf16 1024² / 2048²                            | 40 / 29 GFLOPS (no native bf16: use fp32) |
| matvec fp32 4096×1024 (in L2/L3 cache)             |                                   28 GB/s |
| matvec fp32 8192×8192 (256 MB, DRAM)               |                     **23 GB/s** effective |
| `torch.rand`/`randn` 100M fp32                     |                                     1.1 s |
| `torch.randint` int8 100M                          |                                     0.9 s |
| xorshift32 ×4 lanes, C `-O3`, 1 thread, 100M float |                        0.37 s (1.08 GB/s) |
| PCG32, C, 1 thread, 100M float                     |                        0.39 s (1.03 GB/s) |
| LFSR16 Galois, 1 thread                            |                             245 M steps/s |

Training of a transformer decoder (torch `TransformerEncoderLayer` causal, pre-norm, vocab
4096, T=256, B=16, AdamW, fp32, 4 threads):

| d / L   | Parameters (non-emb) | train tok/s | Effective FLOPS (6N) | Tokens in 8 h |
| ------- | -------------------: | ----------: | -------------------: | ------------: |
| 256 / 4 |          5.3M (3.2M) |       3 016 |                ~95 G |      **~87M** |
| 384 / 6 |        13.8M (10.7M) |         986 |                ~82 G |          ~28M |
| 512 / 8 |        29.4M (25.2M) |         271 |                ~48 G |           ~8M |

Decode-like inference (chain of fp32 matvecs, batch 1, one token):

| Model                   |   tok/s |
| ----------------------- | ------: |
| 30M (d=512, 9 blocks)   | **113** |
| 100M (d=768, 14 blocks) |  **31** |

- Consistent with the bandwidth limit: 100M × 4 B = 400 MB/token → at 23 GB/s ≈ 57 tok/s theoretical.
  int8 (VNNI) halves the bytes: estimate ~50–60 tok/s at 100M. The ≥5 tok/s target has a 6× margin.
- Bursts overestimate the sustained rate: under `bg` + governor expect −20/−40% over hours.

### External references

- TinyStories: ~470M train tokens with the GPT-2 tokenizer
  ([count 471.6M](https://arxiv.org/pdf/2405.17767)); with vocab 4096 (llama2.c `tok4096`)
  the count rises (shorter pieces), order 0.5–0.6B tokens.
- [llama2.c](https://github.com/karpathy/llama2.c): stories15M/42M/110M trained on GPU (A100),
  not on CPU; run.c reaches hundreds of tok/s on stories15M on a desktop CPU.
- Rented GPUs September 2026: RTX 4090 ~$0.34–0.69/h (RunPod community/secure), ~$0.47/h
  Vast.ai; H100 ~$2–3/h ([Spheron](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-runpod-vs-vastai-2026/),
  [RunPod](https://www.runpod.io/pricing), [gpuperhour](https://gpuperhour.com/)); RTX 5090
  spot from ~$0.25/h ([TechRadar](https://www.techradar.com/pro/security/you-can-now-rent-a-usd3000-nvidia-rtx-5090-gpu-from-just-usd0-25-hour-when-you-need-it-for-as-long-as-you-need-it)).

## What is missing

- Training benchmarks for **procedural parameterization**: no public numbers on CPU. The
  dominant cost is the **effective** forward/backward (30–100M), plus weight generation at
  every step (PRNG + linear combination: ~P·N FMA for P bases per block, negligible if P≤8,
  or cached regeneration: the bases are fixed, only the coefficients are trained).
  Estimate: procedural tok/s ≈ dense tok/s at equal effective parameters × 0.6–0.9.
- Real sustained overnight rate under the thermal governor: not measured (needs a 30-min `bg` run).
- Expected quality per token seen: coherent TinyStories models (1–33M) are trained on
  hundreds of millions to billions of tokens; no data on "30M effective with 8M tokens".

## Implication for the thesis

**What trains on CPU in one night (8 h, sustained ~0.7× of bursts):**

- Dense 1–5M: ~60–90M tokens/night (~15% of a TinyStories epoch). Chinchilla ratio ~20
  tokens/param → 5M params saturate in ~1–2 nights. **E0 feasible on CPU.** The dense frontier at
  ~11 Mbit (survey 04) falls right here: 11 Mbit / 4 bits ≈ 2.8M params, / 2 bits ≈ 5.6M.
- Dense/procedural 10–15M effective: ~20M tokens/night. Useful for smoke tests and relative ranking,
  under-trained in absolute terms.
- Procedural 30M effective: ~5–8M tokens/night; 100M effective (d=768): estimated ~50–80 tok/s →
  **~1.5–2M tokens/night**. Two orders of magnitude below what is needed.

**Expansion at boot (F3):**

- PRNG: 100M fp32 weights in ~0.4 s (1 thread) / ~0.1 s (4 threads). With Philox/torch ~1 s.
- Basis×coefficient recombination (SeedLM-like, P=4–8): <1 GFLOP → <0.1 s.
- Neural generator (MLP hypernetwork, h=256 per weight): ~2·h·N ≈ 51 GFLOP → ~0.5–1 s.
- RAM: 100M fp32 = 400 MB (+ a few MB of KV cache at T=256): within 1 GB; 100M int8 = 100 MB.
- **F3 does not trigger** except for generators with >~50 kFLOP/weight (60 s × ~100 GFLOPS / 1e8 weights).
- Generation: 31 tok/s (100M fp32) / 113 tok/s (30M) measured ≫ 5 tok/s.

**When a GPU would be needed (not decided here):** procedural training at 30–100M effective for
≥0.3–1B tokens. Estimate: 6 × 1e8 × 1e9 ≈ 6e17 FLOP; RTX 4090 at ~40 TFLOPS useful bf16 → ~4 h ≈
**$2–3/run**; ×2–3 for procedural overhead; one E3 sweep (3 scales × 3 seeds × 2 arms)
≈ **$30–150**; on H100 the same order of cost, fewer hours. On CPU the same run would take
~6e17 / 5e10 ≈ 140 days.

- **F4** (TinyStories coherence) cannot be evaluated honestly at 100M effective on CPU: the
  model would be under-trained by 100×, and an F4 failure would be confounded with lack of
  compute. This must be declared before E3.
- **F1** can be falsified on CPU at small scale (E1 at 5–15M effective): if the procedural model
  does not beat the dense one there, there is no reason to pay for the GPU.

## Minimum experiment

- **E0** (CPU, feasible): dense frontier 0.5–5M params, quantized 2/3/4/8 bits, complete
  bit-accounting; ~1 night per point, 6–8 points → 1–2 weeks of `bg` nights.
- **E1** (CPU, feasible at reduced scale): procedural at equal `model_bytes`, 5–15M effective,
  same token budget as the dense model (e.g. 60M). Decides F1 before spending.
- **E2** (CPU, cheap): rANS + rate loss applied to both arms; negligible cost compared to
  training (a few minutes of encode/decode).
- **E3** (hybrid): boot-cost measurement at 30–100M on CPU (seconds); quality scaling at
  30–100M effective → **rented GPU** if E1 passes; on CPU only curves truncated at ≤15M.
- **E4** (CPU): real FAT12 image + boot from a clean host, end-to-end measurement of expansion
  time and tok/s.
- Before E0: a 30-min `bg` run at d=256 to pin the real sustained/burst factor.

Later note (2026-10-01): the `bg` instructions above (overnight rate, `bg` nights, 30-min
pin) are superseded by [ADR 0003](../adr/0003-lab-practices.md). Reproduce with
`nohup python` and a log under `runs/`. The 2026-09-30 estimates are unchanged.

Later note (2026-10-08): E0 is not the laptop bit-width sweep in the minimum
experiment. It trains on one Xbox Series S. A rented GPU is not part of the
scientific record ([ADR 0009](../adr/0009-xbox-e0-backend.md)).
