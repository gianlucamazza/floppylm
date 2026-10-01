# Survey 7 — Learned-codebook VQ below one bit: learned vs seed vs ternary at equal rate

Consolidated from web research on 2026-09-30.

## Question

Is there already an LM trained from scratch with vector-quantized weights and a learned codebook below 1
bit/weight, and what is known about learned VQ vs random codebook vs ternary at equal rate?

## What exists

**Post-training VQ on large LLMs (2–3 bits).** Almost all the VQ literature on weights lives here. AQLM
([arXiv:2401.06118](https://arxiv.org/abs/2401.06118), ICML 2024) uses additive quantization with
learned per-block codebooks: at ~2 bits it uses a codebook of 2^15–2^16 entries over groups of 8
weights and takes Llama-2 7B from 5.12 to 6.59 and the 70B from 3.12 to 3.94 WikiText-2 ppl. The
calibration cost is ~1 day on A100 for the 7B, plus 3–6 h of fine-tuning on 4 A100s. The FP16 codebook
costs g·2^B·16 bits per matrix, negligible at 7B, not at 1.44 MB. GPTVQ
([arXiv:2402.15319](https://arxiv.org/abs/2402.15319)) shows the "blessing of dimensionality": at equal
bits, higher-dimensional VQ dominates scalar. The codebook is initialized with data-aware EM and
compressed with int8 and SVD, at a cost of 3–11 h on H100 for the 70B. VPTQ
([arXiv:2409.17066](https://arxiv.org/abs/2409.17066)) is second-order VQ at 2 bits: −0.01/−0.34 ppl on
Llama-2 versus SOTA, 1.6–1.8× better throughput. LCQ
([arXiv:2405.20973](https://arxiv.org/abs/2405.20973)) replaces the rank-one codebook with a low-rank
one and claims "negligible" storage cost. GLVQ
([arXiv:2510.20984](https://arxiv.org/abs/2510.20984)) learns a lattice generator matrix per group and
contains the only clean learned-vs-fixed ablation found. With a shared fixed lattice, Llama-2 7B ppl at
2 bits rises from 5.69 to 5.95; at 1.0 bit on average GLVQ gets 7.83, versus 32.48 for BiLLM, 9.73 for
OneBit and 8.28 for PV-Tuning. On-the-fly sub-block decoding costs 2–3% latency compared to int4.

**Fixed or computed codebooks: the "seed" arm already exists, and it is strong.** QuIP#
([arXiv:2402.04396](https://arxiv.org/abs/2402.04396)) uses a non-learned codebook, the E8 lattice
(E8P, 8 dimensions, 2 bits), after a random Hadamard transform that makes the weights nearly i.i.d.
Gaussian. QTIP ([arXiv:2406.11235](https://arxiv.org/abs/2406.11235), NeurIPS 2024 spotlight) replaces
VQ with trellis quantization (bitshift trellis, L=16), which decouples rate and dimension and reaches an
effective dimension of 256. It is the most important data point for our ablation. The _computed_ codes
1MAD and 3INST generate pseudo-Gaussian values from an LCG in 2–4 instructions and have no parameters.
On a Gaussian source at 2 bits they reach MSE 0.069, versus 0.071 for the _tunable_ hybrid code HYB,
0.089 for QuIP#'s E8P and 0.063 for the distortion-rate bound. On Llama-2 without fine-tuning, at 2
bits, 1MAD and 3INST give identical ppl: 6.82 on the 7B and 3.90 on the 70B, versus 8.22 and 4.16 for
QuIP#, with 23.5 tok/s on the 70B (RTX 6000 Ada). SeedLM
([arXiv:2410.10714](https://arxiv.org/abs/2410.10714)), already discussed in
[Survey 2](02-procedural-weights.md), is the per-block random codebook (LFSR seed plus coefficients),
but stays at 3–4 bits. On Gaussianized weights, then, a high-dimensional pseudo-random code matches or
beats a low-dimensional learned codebook, and costs 0 bytes.

**Below one bit: all post-training or QAT on pretrained models.** BiLLM
([arXiv:2402.04291](https://arxiv.org/abs/2402.04291)) reaches 1.08 average bits (Llama-2 70B ppl 8.41)
in 0.5 h for a 7B. PB-LLM ([arXiv:2310.00034](https://arxiv.org/abs/2310.00034)) binarizes everything
except a fraction of salient weights kept at higher bits. OneBit
([arXiv:2402.11295](https://arxiv.org/abs/2402.11295), NeurIPS 2024) uses ±1 signs plus value vectors
with distillation and retains ≥81% of LLaMA's performance. STBLLM
([arXiv:2408.01803](https://arxiv.org/abs/2408.01803)) is the first structured N:M binarization below
one bit. On LLaMA-2 7B (FP16 5.47) it gives 13.06 at 0.8 bits, 18.74 at 0.7 and 27.93 at 0.55, versus
50.25 and 263.61 for BiLLM; on the 65B (FP16 3.53) it gets 6.43 at 0.8 bits and 11.07 at 0.55. BTC-LLM
([arXiv:2506.12040](https://arxiv.org/abs/2506.12040)) is the closest to our mechanism. It groups
recurring _binary_ vectors into a learned binary codebook (centroids updated by sign, compact indices),
between 0.7 and 1.11 bits, and loses 3.1 zero-shot points at 0.8 bits on LLaMA-2 13B. NanoQuant
([arXiv:2602.06694](https://arxiv.org/abs/2602.06694)) factorizes into low-rank binary matrices via
ADMM (70B compressed 25.8× in 13 h on H100). LittleBit
([arXiv:2506.13771](https://arxiv.org/abs/2506.13771)) does QAT on binarized latent factors down to
0.1 bits/weight and claims that at 0.1 bpw on Llama-2 7B it beats the best method at 0.7 bpw. The
common message is that below one bit ppl explodes even at 7–65B with PTQ, and that only what factorizes
(low-rank binary) or reuses recurring structures (binary codebook) works. None of these trains from
scratch.

**From scratch: 1 bit yes, VQ almost never.** BitNet ([arXiv:2310.11453](https://arxiv.org/abs/2310.11453))
trains 1-bit weights from scratch with BitLinear and shows a scaling law similar to FP16. Ternary b1.58
and its limits below 1B are covered in Surveys [1](01-tiny-lms.md) and [3](03-mdl-compression.md). The
counter-example closest to thesis v0.2 is Quant-Noise (Fan, Stock et al.,
[arXiv:2004.07320](https://arxiv.org/abs/2004.07320), ICLR 2021). A 16-layer Transformer on
WikiText-103 is trained _from scratch_ by quantizing a random subset of blocks at every forward (noise
0.05, blocks of 8) and then compressed with iPQ (Stock-style iterative PQ). It goes from 942 MB (ppl
18.3) to 38 MB (ppl 20.7, versus 25.2 without Quant-Noise): ×24.8, i.e. ~1.3 bits/weight. With layer
sharing it reaches 19 MB and ppl 22.0 (×49.5, ~0.65 bits per effective weight); with pruning 10 MB and
ppl 24.7 (×94, ~0.34). The key data point for training is that QAT with full straight-through on iPQ is
_worse_ than PTQ: ppl 41.2 versus 25.2. The codebook, however, is post-hoc k-means, not learned under a
rate loss, the scale is 247M with a 267k vocabulary, and there is no random-codebook control. Stock et
al. ([arXiv:1907.05686](https://arxiv.org/abs/1907.05686), ICLR 2020) are the reference weight PQ:
ResNet-50 in 5 MB (×20, ~1.6 bits/weight) at 76.1% top-1, Mask R-CNN ×26, vision only. DKM
([arXiv:2108.12659](https://arxiv.org/abs/2108.12659), ICLR 2022) makes k-means differentiable with
weight→centroid attention and joins weights and centroids. It gets MobileNet-v1 in 0.72 MB (63.9%) and
DistilBERT ×11.8 with −1.1% on GLUE, but training memory is prohibitive for LLMs: eDKM
([arXiv:2309.00964](https://arxiv.org/abs/2309.00964)) reduces it by 130× to bring LLaMA-7B to 3 bits,
again from pretrained. Soft-to-Hard VQ ([arXiv:1704.00648](https://arxiv.org/abs/1704.00648)) is the
"VQ + entropy annealing" precursor of the MDL loss (Survey 3), vision only. Sign Lock-In
([arXiv:2602.17063](https://arxiv.org/abs/2602.17063), ICML 2026) is the only from-scratch sub-bit work
on text I found. It shows that weight signs stay those of the random initialization, because flips only
happen through rare crossings near zero, and that below 1 bpw the signs are the incompressible
bottleneck. Training from scratch with a regenerable rank-2 sign template, a CharLM keeps ppl at
~0.5–0.7 bpw and flips drop to ~10⁻³ for about +1 ppl point. It is not VQ, but it is direct evidence
that part of the sub-bit description can come from a seed.

**Learned vs random outside LM weights.** The evidence is split. Variable Bitrate Neural Fields
([arXiv:2206.07707](https://arxiv.org/abs/2206.07707), SIGGRAPH 2022) finds that learned indices (VQ
auto-decoder) need far fewer bits than random hashing at equal quality, up to 100× less memory. Random
Entity Quantization ([arXiv:2310.15797](https://arxiv.org/abs/2310.15797), EMNLP 2023) instead finds
that assigning random codewords to KG entities matches learned strategies, because random codes have
more entropy and distinguishability. FSQ ([arXiv:2309.15505](https://arxiv.org/abs/2309.15505)) shows
that a _fixed_ codebook (low-dimensional scalar grid) matches learned VQ in VQ-VAEs without collapse and
without commitment loss, reseeding or entropy penalty. "Only relative ranks matter"
([arXiv:2603.17917](https://arxiv.org/abs/2603.17917)) clusters Llama-3.1-8B and SmolLM2-135M to 16–64
values per matrix. Randomizing the centroids while preserving the order costs almost nothing in middle
and late layers; shuffling the ranks destroys the model; fine-tuning the centroids recovers only 30–40%
of the residual gap. The exact codebook values therefore matter little, its structure a lot.

**Embedding (28% of the bits at d=384, V=2048).** Shu & Nakayama
([arXiv:1711.01068](https://arxiv.org/abs/1711.01068), ICLR 2018) learn compositional multi-codebook
codes end-to-end via Gumbel-softmax: −98% on the embedding in sentiment, −94–99% in translation. DPQ
([arXiv:1908.09756](https://arxiv.org/abs/1908.09756), ICML 2020) makes embedding PQ differentiable,
drop-in, with ×14–238 at negligible cost. CARVQ
([arXiv:2510.12721](https://arxiv.org/abs/2510.12721), EMNLP Findings 2025) does group RVQ plus a small
corrective MLP, post-training, nearly lossless at ~2.4 bits and usable at ~1.6. VQ-Logits
([arXiv:2505.10202](https://arxiv.org/abs/2505.10202)) claimed −99% on the output layer with +4% ppl,
but was withdrawn on 18/9/2026 for insufficient experiments and must not be used. The work on fixed
binary input codes ([arXiv:2605.09751](https://arxiv.org/abs/2605.09751)) is already in Survey 2: on
the input side the random codebook is free and loses nothing.

**Parameter Golf** ([repo](https://github.com/openai/parameter-golf)), all at 16 MB. PR
[#1433](https://github.com/openai/parameter-golf/pull/1433) "Codebooks!" uses QuIP#'s fixed E8P
codebook, chosen precisely to avoid storing the codebook ("saves 1–2 MB"). 16-bit indices on blocks of
8 plus an 8-bit scale make 3.0 bpw, and the quantization gap stays large (pre-quant 1.104, post 1.224,
1.2067 sliding over 3 seeds). The author reports that going below 2 bpw gives incoherent models, that
multiple or AQLM-style residual codebooks are hard to optimize, and that QAT with VQ in the forward is
too slow. They also note that an entropy penalty on the assignment reduces bytes but hurts more, and
that simple periodic "snapping" to the codebook works better than more sophisticated methods. PR
[#1335](https://github.com/openai/parameter-golf/pull/1335) co-trains a VQ codebook (G=2, K=1024,
sphere, EMA 0.95, reseeding of dead entries) during warmdown, at 5 bpw. The quantization delta is
+0.0018 bpb, versus +0.0024 for post-hoc k-means and +0.0049 for INT5: learned-in-training beats
post-hoc by only 0.0006 bpb. PR [#212](https://github.com/openai/parameter-golf/pull/212) measures that
k-means K=256 has −87% MSE versus int6 but produces a +25% larger artifact after zstd, because the
indices have high entropy. PR [#532](https://github.com/openai/parameter-golf/pull/532) recovers 21%
with per-tensor codebooks plus Huffman. PR [#1515](https://github.com/openai/parameter-golf/pull/1515)
(Hessian-weighted k-means at int3) gets 1.0872 and shows a floor for scalar at 16 MB. On binary from
scratch, PR [#2048](https://github.com/openai/parameter-golf/pull/2048) gets 1.3551 and the XNOR-Net of
[#1388](https://github.com/openai/parameter-golf/pull/1388) 1.539. No PR does sub-bit VQ, neither
learned nor random, nor VQ from scratch.

## What is missing

Web queries: "language model trained from scratch vector quantized weights learned codebook sub-1-bit",
"quantization-aware training vector quantization codebook transformer weights from scratch", "sub-1-bit
LLM compression 2025", "weight clustering k-means codebook trained from scratch small language model
TinyStories", "vector quantized weights pretraining LLM codebook 2026", "sub-1-bit language model
pretraining from scratch", "learned codebook versus random codebook equal bitrate", "random fixed
codebook vs learned codebook LLM ablation". On Parameter Golf I searched with `gh pr list --state all`
for the terms vector quantization, VQ, codebook, k-means, kmeans, product quantization, lattice, E8,
trellis, QTIP, AQLM, clustering, sub-bit, binary, "codebook QAT", "random codebook".

The bounded search above did not identify the full counter-example. No reviewed work trains from scratch a small LM (≤30M) with VQ weights
and a learned codebook below 1 bit/weight, and none compares at equal rate, with the codebook bytes
counted, learned codebook vs seeded codebook vs ternary. The pieces exist separately. From scratch there
are binary (BitNet), sub-bit non-VQ (Sign Lock-In, CharLM) and PQ at ~1.3 bits with noise but a post-hoc
codebook (Quant-Noise). Sub-bit with a learned codebook exists only post-training (BTC-LLM, GLVQ at 1.0
bit). The learned-vs-computed comparison exists only post-training at 2 bits, and there the computed one
wins or ties (QTIP); the only ablation in the opposite direction is GLVQ (+0.26 ppl with the fixed
lattice), also post-training. Also missing is the accounting of codebook bytes in the regime where they
matter. With 11 Mbit, an FP16 codebook of 2^16 × 8 (AQLM's) costs 8 Mbit on its own.

## Implication for the thesis

**F0.** See verdict. The combination "learned VQ + from scratch + below one bit + tiny LM + seed control
at equal rate + recursion" is a candidate comparative contribution; none of its components is new.

**F1** (learned VQ + recursion does not beat by ≥max(0.02, 2σ) the best of ternary/2-bit dense and
ternary recursion at equal bytes). The prior is unfavorable for three reasons. First, below one bit PTQ
ppl explodes even at 7–65B (STBLLM 0.55 bits: ×5 the ppl of the 7B), and from scratch the only sub-bit
LM (Sign Lock-In) stays on the CharLM. Second, Parameter Golf did not close the VQ gap even at 3 bpw
(#1433: +0.12 bpb) and found binary and XNOR clearly worse than int6. Third, in Quant-Noise the step
below one bit per effective weight comes from _sharing_ (19 MB, ppl 22.0), not from more aggressive PQ.
The argument in favor is that ternary at 1.58 bits gives ~7M parameters, while at 0.5 bpw the ~7 Mbit of
the core are worth ~14M weights, ×4 with recursion.

**F1-ablation (learned ≈ seed).** It is likely to trigger, and it is the most informative result of the
survey. QTIP shows that on Gaussianized weights a computed pseudo-random code matches the tunable one
(MSE 0.069 vs 0.071, identical ppl between 1MAD and 3INST). FSQ and Random Entity Quantization show the
same outside weights, and "Only relative ranks matter" that the exact centroid values matter little.
Moreover, from scratch the weights _co-adapt_ to the codebook: QAT moves the weights toward the
available cells, and this erodes the advantage of a tailored codebook, which in PTQ exists only because
the weights are fixed beforehand. Finally, the learned codebook pays bytes that the seed does not. At
rate R = log₂K/d it costs K·d·b_c bits: at R=0.5 with d=16, K=256 and b_c=8 that is 4 KB (negligible),
but with d=24, K=4096 it is ~98 KB, 7% of the floppy. High-dimensional VQ, where GPTVQ and QTIP say the
gain lies, is accessible at zero cost only with computed codes. The learned arm must therefore be
structured: a single codebook shared across layers (#1433 finds that sharing works), a GLVQ-style
lattice generator or LCQ-style low rank. A free K per layer does not hold up.

**F2** (the advantage vanishes with the same entropy coding for all). The risk is concrete and
asymmetric. VQ indices have near-maximal entropy: #212 finds k-means indices _less_ compressible than
int6 under zstd, and #1433 that forcing code reuse costs quality. Ternary instead gains from coding
because it is sparse (BITCOS 1.485 bits, Survey 3). VQ therefore cashes in little from E2, the baselines
a lot, and the comparison must be made on coded bytes, not nominal bits.

**F3** (boot). Not a threat. VQ decoding is a gather: N/d table reads, i.e. 14M weights at d=16 make
<1M gathers, milliseconds. A seeded codebook needs K·d PRNG draws (≤10⁵), a QTIP-style computed code
2–4 instructions per weight with no table. Expanding 14M weights to fp32 takes 56 MB of RSS, but it can
be avoided by decoding on the fly in sub-blocks (GLVQ: 2–3% latency, peak memory ÷10). With recursion
the cost is paid only once per shared block.

**F4** (coherence). VQ does not touch F4 directly, but if F1 triggers the effective parameters stay
~7M and the TinyStories coherence threshold (10–30M, Survey 1) stays out of reach.

**Cost of VQ-QAT training.** The classic VQ-VAE (commitment β≈0.25, EMA of centroids) collapses: dead
entries must be reinitialized (#1335 replaces them after 5 unused snaps), and the known causes are the
straight-through bias, "one step behind" updates and sparse codebook gradients
([arXiv:2509.10140](https://arxiv.org/abs/2509.10140)). The rotation trick
([arXiv:2410.06424](https://arxiv.org/abs/2410.06424)) improves gradients and utilization, FSQ removes
the problem by fixing the codebook. On weights, full STE can be worse than PTQ (Quant-Noise 41.2 vs
25.2), while quantizing a random subset per step costs <5% of time. Nearest-neighbor assignment costs
N·K flops per step, i.e. 5.7·10¹⁰ with N=14M and K=4096, ~3% of the forward of a 64k-token step
(2·N·T ≈ 1.8·10¹² flops): acceptable, but on this laptop better every k steps. Full DKM requires
O(N/d·K) memory, which eDKM had to reduce by 130×.

**What changes for thesis v0.2.** (1) The seed control arm is not a weak baseline but the a-priori
favorite. It is worth preregistering that the "learned codebook" thesis holds only if it beats the seed
by ≥2σ _including the codebook bytes_. (2) A third arm with a high-dimensional computed code is needed
(QTIP bitshift trellis, fractional rates without a table), because it dominates 8D VQ at equal rate.
(3) The training recipe must use Quant-Noise or periodic snapping with reseeding, not pure STE. (4)
Below one bit the signs are the bottleneck: seeded-template signs (Sign Lock-In) plus VQ magnitudes is a
natural seed/learned hybrid to try. (5) For the embedding the literature already gives ×14–238 with
learned PQ/compositional codes and a free random input: the embedding's 28% is the easiest target, but
it is not the novelty.

## Minimum experiment

It is a restricted E1, before E2. On TinyStories with V=2048, d=384 and a fixed core budget of 7 Mbit
(exact bytes including codebook, scales and indices), 3 seeds and 3 rates (0.5, 0.75, 1.0 bpw), five
arms are trained from scratch with the same recursion (k shared blocks × r iterations):

- (a) VQ with a single shared learned codebook (d=8/16, K=2^(Rd), EMA plus reseeding, Quant-Noise p=0.05);
- (b) the same VQ with a frozen seeded codebook (Gaussian, same per-row scale);
- (c) QTIP-style computed 1MAD/3INST trellis;
- (d) ternary QAT at equal bytes;
- (e) 2-bit QAT at equal bytes, these last two as F1 baselines.

We measure validation bpb, coded bytes (also with rANS for all, anticipating E2), assignment time per
step and boot/decoding time on the C binary. F1-ablation triggers if |a−b| < max(0.02, 2σ) at all
rates; F1 triggers if min(a, b, c) does not beat min(d, e) by max(0.02, 2σ). If (b) or (c) ≥ (a), the
thesis is rewritten as "seeded VQ + recursion" and the learned codebook is reduced to an ablation.

**F0 verdict: partial.** It does not fully trigger. No work found trains from scratch an LM with VQ
weights and a learned codebook below 1 bit/weight, and none compares learned and seed at equal rate
counting the codebook bytes, let alone in a tiny LM with recursion. One cannot, however, say "it does
not trigger". The individual pieces are published and must be cited as state of the art:

- Quant-Noise: from-scratch PQ-aware LM at ~1.3 bits, ~0.65 per effective weight with sharing;
- Sign Lock-In: from-scratch LM at 0.5–0.7 bpw, with signs from a template;
- BTC-LLM and GLVQ: learned codebook at 0.7–1.0 bit, post-training;
- QTIP: computed random code ≈ tunable codebook;
- Parameter Golf #1335 and #1433: co-trained or fixed codebook on LMs, at 3–5 bpw.

The claimable novelty is the controlled byte-exact comparison in the sub-1.5 MB regime, not the
mechanism. The literature's prior is that the learned codebook will _not_ beat the seeded one.
