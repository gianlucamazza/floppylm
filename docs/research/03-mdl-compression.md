# Survey 3 — MDL, weight coding and the price of an LM in bits

Consolidated from web research on 2026-09-30.

> **Framed for thesis v0.1.** Its "Minimum experiment" section predates [concept v0.2](../concept.md); E0–E4 are defined only by the [roadmap](../roadmap.md).

## Question

How many bits does an LM cost, counting model and decompressor, and does rate-aware training (NLL + λ·bits
of the weights, with entropy coding) move the bpb-per-byte frontier compared to quantizing and
compressing afterwards?

## What exists

**MDL framework.** Hinton & van Camp (COLT 1993,
[doi:10.1145/168304.168306](https://doi.org/10.1145/168304.168306)) formulate training as minimizing the
description length of weights plus errors, with noisy weights whose cost is a KL (bits-back). Blier &
Ollivier ([arXiv:1802.07044](https://arxiv.org/abs/1802.07044), NeurIPS 2018) actually measure these
code lengths: the variational code is "surprisingly poor" (MNIST 24.1 kbit, CIFAR-10 89.0 kbit for the
labels, model included), while the prequential code (train online and encode each block with the
current model) gets down to 4.10 kbit and 45.3 kbit, i.e. 6× and 2× better. The limitation, decisive for
us, is that the prequential code does not transmit the weights: the receiver retrains them on the data
it is decoding. For an artifact that must generate text without data, only the two-part code (weights +
NLL) remains applicable, which is precisely the regime in which deep networks compress worst. MIRACLE
([arXiv:1810.00440](https://arxiv.org/abs/1810.00440)) makes bits-back practical with random-sample
coding: LeNet-5 in 1.52 KB (1110×, error 0.96%) and VGG-16 CIFAR in 135 KB (452×).

**Trained entropy coding.** Deep Compression
([arXiv:1510.00149](https://arxiv.org/abs/1510.00149)) shows that pruning + cluster quantization +
Huffman gives 35–49× (AlexNet 240→6.9 MB, VGG-16 552→11.3 MB); on LeNet quantization alone gives ~32×
and Huffman brings it to ~40×. Oktay et al. ([arXiv:1906.06624](https://arxiv.org/abs/1906.06624), ICLR 2020) are the direct methodological reference for the "rate-aware loss": parameters in a latent space
with a learned probability model, entropy penalty during training and arithmetic coding at the end, in
a single stage. They get LeNet-5 in 2.84 KB (606×) and ResNet-18 ImageNet in 1.97 MB (24×) at equal
error, comparing against Bayesian Compression and DeepCABAC. Self-Compressing Neural Networks
([arXiv:2301.13142](https://arxiv.org/abs/2301.13142)) learn the per-channel bit depth with a size
penalty and keep float accuracy with 3% of the bits and 18% of the weights. On the recent LLM front,
entropy coding is almost always post-training. Neural Weight Compression
([arXiv:2510.11234](https://arxiv.org/abs/2510.11234)) uses learned transforms and entropy-constrained
quantization, strong at 4–6 bits; EntroPack ([arXiv:2609.34185](https://arxiv.org/abs/2609.34185)) uses
an E8 lattice with a conditional model at arbitrary bitrate (−24% L2 error versus NF4 at 4 bits);
[arXiv:2606.15789](https://arxiv.org/abs/2606.15789) measures an effective entropy 2–10× below the
nominal bit width on LLMs from 1.5B to 405B and reaches it with rANS within 0.01–0.1 bits of the Shannon
limit.

**Model counted in the score: LM as compressor.** Delétang et al.
([arXiv:2309.10668](https://arxiv.org/abs/2309.10668), ICLR 2024) show that Chinchilla 70B compresses
enwik9 to 8.3% (≈0.66 bpb) if the model is free, but to 14 008% if the parameters are counted at 2 bytes
each. For each dataset there is a critical size beyond which the "adjusted" rate gets worse, and the
optimal size depends on the size of the text to compress. This is the heart of the FloppyLM question:
with 11.8 Mbit available, the "model bits" term dominates. The Large Text Compression Benchmark
([LTCB](https://www.mattmahoney.net/dc/text.html)) and the Hutter Prize
([prize.hutter1.net](http://prize.hutter1.net/), where the sum compressor + self-extracting archive
counts) give concrete numbers. The accepted record is fx2-cmix (Orav & Knoll, September 2024), 110
793 128 total bytes on enwik9, ≈0.886 bpb. Among the 2026 entries under verification,
fx2-cmix-transformer (Ivanov, July 2026) replaces the online LSTM with a 6M-parameter Transformer
pretrained offline (8 RTX 5090 for 26 h), quantized to 4-bit weights / 8-bit activations, which adds
2.9 MB to the binary: archive 96 996 198 + compressor 3 428 474 bytes, ≈0.803 bpb. zmix (September 2026)
and cmix-lex-transformer lexth11c (27 September 2026, 95 836 613 + 3 477 137 = 99 313 750 bytes,
≈0.795 bpb) retrain those "quantization-optimized" weights. It is the first time a two-part model with
stored pretrained weights, rather than a purely online one, wins in the Prize. NNCP (Bellard,
[bellard.org/nncp](https://bellard.org/nncp/); v3.2 in the LTCB, v3.3 current) remains prequential:
Transformer trained during (de)compression, 628 955-byte decompressor, enwik8 14 915 298 bytes
(≈1.193 bpb) and enwik9 106 632 363 bytes (≈0.853 bpb). cmix v21 does enwik8 in 14 623 723 bytes
(≈1.170 bpb).

**Fixed byte budget for a generative LM: Parameter Golf.** The OpenAI challenge
([repo](https://github.com/openai/parameter-golf), [arXiv:2607.01517](https://arxiv.org/abs/2607.01517))
measures bpb on FineWeb with an artifact (code + compressed weights) ≤16 MB. Over 2 037 PRs the frontier
drops from 1.2244 (int8 + zlib, 9 layers × 512) to 1.058, and the contribution analysis points to int6
with QAT-STE (frees ~4 MB), plus GPTQ and Brotli, as the reliable choice. Ternary turns out neutral and
binary negative: "very-low-bit formats give up more than the freed budget can recover". Concrete points:
ternary 73.7M parameters 1.157 bpb in the 10-minute track; binary 106M parameters with 2 h of training
1.1239; BitNet 68M ternary packed at 1.6 bits/param in 15.88 MB 1.177
([#367](https://github.com/openai/parameter-golf/pull/367)). On ternary, that PR reports that almost the
whole standard stack (weight decay, XSA, SWA) "breaks or doesn't help". QAT with entropy regularization
toward the grid halves the quantization gap from 0.017 to 0.009 bpb
([#885](https://github.com/openai/parameter-golf/pull/885)); an entropy penalty on the weights improves
the SWA average by 0.028 bpb ([#459](https://github.com/openai/parameter-golf/pull/459)); a PR for
entropy-regularized QAT on the quantized symbols stayed WIP
([#930](https://github.com/openai/parameter-golf/pull/930)). The leaderboard also shows a methodological
risk: n-gram caches and test-time training in evaluation produced "records" at 0.08–0.4 bpb, so the
evaluation protocol must be fixed before comparing numbers.

**Ternary and low bit as a rate point.** BitNet b1.58
([arXiv:2402.17764](https://arxiv.org/abs/2402.17764)) trains from scratch with weights {−1,0,1} and
claims perplexity parity with FP16 at equal size and tokens (in the paper, from ~3B parameters).
Spectra/TriLM ([arXiv:2407.12327](https://arxiv.org/abs/2407.12327)) finds that ternary models beat
float and quantized ones at equal bits only above ~1B parameters: the 3.9B TriLM matches the 3.9B
FloatLM with fewer bits than the 830M FloatLM. ParetoQ ([arXiv:2502.02631](https://arxiv.org/abs/2502.02631),
NeurIPS 2025) unifies sub-4-bit QAT: ternary, 2 and 3 bits are comparable in the size/accuracy trade-off
and generally beat 4 bits and binary, with a learning transition between 2 and 3 bits. Scaling Laws for
Precision ([arXiv:2411.04330](https://arxiv.org/abs/2411.04330)) models low precision as a reduction of
effective parameters and shows that post-training quantization degradation grows with pretraining
tokens, which favors QAT from the start for heavily trained models. BITCOS
([arXiv:2609.16338](https://arxiv.org/abs/2609.16338)) measures up to 51.5% zeros in 29 ternary LLMs and
stores them at 1.485 bits/weight, below the nominal log₂3 = 1.585: ternary is not a fixed rate point,
and sparsity makes it entropy-codable.

**Orders of magnitude for the floppy.** 1 474 560 bytes are 11.80 Mbit. Minus ~50–100 KB of runtime and
tokenizer, about 2.7–2.9M parameters at 4 bits remain, ~7.0–7.3M ternary packed at 1.6 bits, or ~8–9M
ternary entropy-coded at ~1.3 bits if sparsity is as high as in BITCOS. At TinyStories scale
([arXiv:2305.07759](https://arxiv.org/abs/2305.07759)) 1–3M models already generate fluent but not very
coherent text, while narrative coherence emerges around 10–30M. The jump the FloppyLM thesis must buy
with the procedural description is therefore about one order of magnitude of effective parameters. As
Survey 1 documents, those counts exclude the embedding table (vocab 50 257, ~3.2M parameters in the 1M
alone), so the vocabulary must be reduced and counted in the budget.

## What is missing

I searched for "entropy-penalized training language model from scratch", "rate-distortion transformer
weights training", "compressible transformer arithmetic coding bits per parameter" and, inside Parameter
Golf, PRs on entropy regularization, compressibility, Brotli, ternary and BitNet. I found no LM trained
from scratch with an explicit NLL + λ·(coded weight bits) loss, Oktay-2020 style, evaluated in bpb per
total artifact bytes. Oktay, MIRACLE and Self-Compressing are validated on vision CNNs. The entropy
methods for LLMs (NWC, EntroPack, BITCOS, rANS) are post-training. In Parameter Golf entropy appears only
as an auxiliary QAT regularizer (#885, #459) and the explicit attempt (#930) has no results. The frontier
under 2 MB is also missing: Parameter Golf lives at 16 MB, the Hutter Prize at ~100 MB with a 2.9 MB
model that however works inside a context mixer (it is not a standalone generative LM), and the
TinyStories points under one MB (stories260K, Single Floppy 346K) are FP32 dense with no coding at all.
The missing piece is the bpb vs total bytes curve between 0.3 and 1.5 MB, with 2–4-bit QAT, ternary,
entropy coding and rate loss applied uniformly. There is not even a measurement of how much the rate
loss adds compared to "QAT + downstream Brotli/rANS", which in Parameter Golf is already strong.

## Implication for the thesis

**F2** is the most exposed condition. The literature says that entropy coding and low bit with QAT,
applied to the dense model, are already very effective (Deep Compression +25% from Huffman; BITCOS below
1.585 bits; int6 QAT + Brotli dominant in Parameter Golf). Any procedural advantage must therefore be
measured against a dense model receiving the same coding, otherwise it is an artifact of the baseline.
The rate loss is a method applicable to all arms, not an advantage specific to procedural weights.
**F1**: ternary is barely competitive below 1B (Spectra) and neutral at 16 MB (Parameter Golf), while
ParetoQ points to 2–3 bits as optimal. The correct dense baseline for the floppy is therefore 2–3-bit
QAT or ternary with entropy coding, not naive int4, and this raises the bar for the procedural models.
**F4**: 2.8–9M dense effective parameters straddle the TinyStories coherence threshold, so F4 is not a
given even for the dense model, and that is where a larger effective model should pay off. Finally, the
prequential code (NNCP, Blier & Ollivier) suggests a control the thesis does not consider:
"description = compressed corpus + trainer", with training at boot. It is almost certainly worse (1.4 MB
compressed is a few million tokens) and violates F3, but it bounds the MDL limit from below and costs
little.

## Minimum experiment

E0 fixes the protocol: bpb on TinyStories validation with no cache or TTT in evaluation, bytes counted
from the final image (coded weights + probability tables + tokenizer + runtime), at least 3 seeds. Then
it measures the dense frontier at 0.5 / 1.0 / 1.44 MB for int4, 3 bits, 2 bits and ternary in QAT, each
with downstream Brotli/zstd and with rANS on quantized symbols. E2 adds to every arm, dense, recursive
and procedural, the same rate loss (entropy of the quantized symbols under a learned factorized prior,
Oktay-style; λ swept) and records the frontier shift. The survey question is answered if, at equal
bytes, "rate loss + rANS" beats "QAT + Brotli" by a margin greater than seed-to-seed variance. F2
triggers if E1's procedural advantage vanishes when the dense model also receives rate loss + entropy
coding + pruning. The prequential control (compressed corpus + trainer) goes into E2 as a single table
row, with boot time noted for E3.

Later note (2026-10-08): E0 does not sweep int4, 3-bit and 2-bit image sizes at
0.5, 1.0 and 1.44 MB. The accepted dense baseline is the roadmap scalar campaign.
Rate loss and rANS stay at E2. This survey does not own the measured numbers.
