# Survey 5 — Evaluating tiny models at equal bytes without room to cheat

Consolidated from web research on 2026-09-30.

> **Framed for thesis v0.1.** Its "Minimum experiment" section predates [concept v0.2](../concept.md); E0–E4 are defined only by the [roadmap](../roadmap.md).

## Question

How do we compare tiny models at equal bytes on disk, so that the comparison between a procedural model
and the dense frontier cannot be rigged through the tokenizer, the data, or the accounting?

## What exists

**Bits-per-byte versus perplexity.** Per-token perplexity is not comparable across different
tokenizers: a larger vocabulary makes longer tokens and changes the per-token loss even at equal
predictive capacity. The Pile (Gao et al. 2020, [arXiv:2101.00027](https://arxiv.org/abs/2101.00027))
codified UTF-8 bits per byte as the preferred metric, BPB = (L_T/L_B)·ℓ/ln 2, where ℓ is the mean loss in
nats per token, L_T the tokens and L_B the UTF-8 bytes of the evaluated text, motivating it with
tokenizer invariance and the ambiguity of "character" in Unicode (for GPT-2 on the Pile, L_T/L_B ≈
0.293). For us this is indispensable: candidates will have vocabularies from 256 (byte-level) to 2048
tokens and a procedural model might use yet another tokenizer. BPB must be computed on the original text
and the tokenizer must round-trip exactly byte→token→byte; a tokenizer that normalizes (lowercasing,
whitespace, discarded rare characters) artificially lowers the loss and must be disqualified or
penalized by counting the lost bytes.

**Compression as a measure.** Delétang et al., "Language Modeling Is Compression" (ICLR 2024,
[arXiv:2309.10668](https://arxiv.org/abs/2309.10668)), make the prediction↔lossless compression
equivalence explicit (Chinchilla 70B compresses ImageNet patches to 43.4% and LibriSpeech to 16.4%,
better than PNG and FLAC) and, above all, introduce an _adjusted_ compression rate that adds the model
size in bytes: with this accounting, for each dataset there is a critical size beyond which the
parameters weigh more than they save, and "the dataset size imposes a hard limit on model size". Huang et
al., "Compression Represents Intelligence Linearly" (COLM 2024,
[arXiv:2404.09937](https://arxiv.org/abs/2404.09937)), on 31 public LLMs and 12 benchmarks find a
Pearson correlation of about −0.93 between bits per character on external corpora and mean downstream
score (−0.94/−0.95 for knowledge, code, math). Two methodological choices are worth copying: evaluation
corpora collected after the cutoff of all models (Common Crawl, GitHub, arXiv from September–October 2023) to avoid contamination, and a single context window (1900 tokens) for all because a longer context
favors compression. The stated caveat is that the result holds for well-trained base models and in a
short-to-medium context regime; nobody has verified it below 10M.

**Hutter Prize and LTCB: the decompressor counts.** The Hutter Prize ([Wikipedia](https://en.wikipedia.org/wiki/Hutter_Prize),
[rules](http://prize.hutter1.net/hrules.htm)) measures enwik9 (10⁹ bytes of Wikipedia) as the archive
size _plus_ the decompressor executable size; the current record is fx2-cmix by Orav and Knoll,
110 793 128 bytes (September 2024), with execution constraints (≲50 hours on one core, <10 GB RAM, no GPU)
and a ban on any external information at decompression time (network, installed corpora, operating system
data). Mahoney's Large Text Compression Benchmark
([textrules](https://www.mattmahoney.net/dc/textrules.html)) counts the compressed file plus the zip of
the decompressor with dictionaries, configuration files and non-standard libraries, choosing the smaller
of executable and source. This is exactly the rule FloppyLM needs: the procedural generator, the tables
and the runtime _are_ part of the model, and information taken from the host system is theft of bits.

**TinyStories and the GPT judge.** Eldan & Li ([arXiv:2305.07759](https://arxiv.org/abs/2305.07759))
evaluate generation by asking GPT-4 to grade the completion "like a teacher", with scores out of 10 for
grammar, creativity, consistency with the beginning (and plot/instruction adherence in the Instruct
variant), on hand-written prompts outside the training set. SimpleStories
([arXiv:2504.09184](https://arxiv.org/abs/2504.09184)) repeats the scheme with GPT-4o-mini,
chain-of-thought, a 0–100 scale and N=200 samples. The LLM judge is however manipulable: Wang et al.,
"Large Language Models are not Fair Evaluators" ([arXiv:2305.17926](https://arxiv.org/abs/2305.17926)),
show that by swapping the presentation order Vicuna-13B beats ChatGPT on 66 of 80 queries with ChatGPT as
judge, and propose evidence calibration, position balancing and human review of high-entropy cases. The
judge must therefore be pinned per version, used in absolute per-sample evaluation and anchored to a
reference model evaluated in the same session.

**BLiMP and the BabyLM pipeline.** BLiMP (Warstadt et al., TACL 2020,
[ACL](https://aclanthology.org/2020.tacl-1.25/)) contains 67 paradigms of 1000 minimal pairs generated
from grammars, with 96.4% human agreement; the model "passes" a pair if it assigns higher probability to
the acceptable sentence, so the metric is purely probabilistic and independent of sampling. The BabyLM
2025 pipeline ([github.com/babylm/evaluation-pipeline-2025](https://github.com/babylm/evaluation-pipeline-2025),
[findings](https://aclanthology.org/2025.babylm-main.28/)) for the strict and strict-small tracks uses
BLiMP, BLiMP supplement, EWoK, COMPS, entity tracking (reformulated as choosing the most probable
continuation) and English Global PIQA, with intermediate checkpoints and a compute budget. The limitation
for us is that BLiMP uses adult vocabulary outside the TinyStories domain: a 2–7M model trained on
children's stories will be near chance on many paradigms for vocabulary reasons, not syntax. It should
only be used as a secondary diagnostic, on a subset filtered by the corpus vocabulary.

**Splits and contamination.** The TinyStories dataset is contaminated: according to Pearce et al.
([arXiv:2406.03947](https://arxiv.org/abs/2406.03947), App. C.3) ~15% of training samples are
duplicates and ~30% of the validation set appears in training; the authors merge train and validation,
remove exact duplicates, reshuffle and re-split. Any bpb computed on the official validation set rewards
memorization, and rewards it most precisely for models with more effective parameters, i.e. the expanded
procedural model: a bias that would inflate F1 in favor of the thesis.

**The baseline must be good.** "Baseline Shape Decides the Verdict" (2026,
[arXiv:2609.29397](https://arxiv.org/abs/2609.29397)) shows that at a fixed byte budget, transformers
with the same number of parameters differ by 22.6% in validation loss from shape alone, that a previous
comparison left the positional embeddings of the baseline in full precision (11–22% of the parameters),
making it "less quantized", and that the advantage of a training regime flips sign with the learning
rate. It is the catalog of ways an equal-byte comparison gets rigged unintentionally.

## What is missing

There is no published protocol that combines held-out bpb, Hutter-style "everything needed to generate
is in the budget" accounting and a generative coherence threshold for models under 10M. We searched for
counter-examples to the plan of using bpb as the primary metric: evidence that at tiny scale bpb and
judged coherence diverge (TinyStories instead shows that all GPT-4 scores rise as loss falls, with
grammar saturating first), and studies validating Huang's correlation below 100M (none found). We also
searched for public bpb for the TinyStories/llama2.c checkpoints (only per-token loss with different
tokenizers, not comparable) and an evaluation of the GPT-4 judge against human scores on children's
stories (only generic evidence of inflation and position bias). Finally, a convention on what counts as
an admissible "host system" is missing: kernel and libc yes, but Python, PyTorch or a system BLAS would
make the runtime free, and no source regulates this for local models.

## Implication for the thesis

The primary metric is held-out bpb computed _from the artifact_, not from the PyTorch checkpoint: the
runtime on the image produces the log-probabilities that the harness sums, so any discrepancy between the
declared model and the expanded model surfaces. The proposed set is this. **(M1) bpb** = Σ NLL in bits /
UTF-8 bytes on a test split derived from TinyStories deduplicated (exact and near-duplicate on 13-grams)
and re-split by text hash, plus a second out-of-distribution test of stories generated after the end of
training with the same vocabulary; fixed context (512 byte-equivalents) with a sliding window, whole
documents, the same for all; tokenizer with verified byte-exact round-trip. **(M2) accounting rule**:
B_total = sum of the clusters allocated on the FAT12 image (≤1 457 664 usable bytes out of 1 474 560
raw), comprising the static executable of the runtime and expander, tokenizer, weights/seeds/coefficients
and every table; allowed from the host system only the x86-64 Linux kernel, libc and CPU, no network, no
external files, no numerical libraries; the F1 comparison is at equal B_total within 1%, reported as a
bpb-vs-B_total curve, and expansion must be deterministic (hash of the expanded weights identical over 5
boots). **(M3) equal treatment** for F2: same corpus, same training tokens, same hyperparameter and shape
search budget, same weight pruning and entropy-coding pipeline applied to every candidate. **(M4) boot
cost** for F3: expansion time from mount to first token ≤60 s, peak RSS ≤1 GB, ≥5 tok/s median over 5
runs on i7-1165G7 at 4 threads with declared governor and thermal state (the background slice is
throttled by the thermal governor, so measurements must be taken outside it). **(M5) coherence** for F4:
50 held-out story-opening prompts, 4 samples each at temperature 0.8/top-p 0.9, LLM judge at a pinned
version in blind absolute evaluation with randomized order, grammar and coherence scores out of 10; F4
triggers if the model fails to reach non-inferiority (0.5-point margin) against
`roneneldan/TinyStories-8M` evaluated in the same session, or falls below the absolute floor grammar ≥6
and coherence ≥5, with a blind human check on 30 samples and a repeated-4-gram rate as a mechanical alarm
against degeneration. Filtered BLiMP and BabyLM entity tracking are diagnostics, not criteria. With
respect to F0, the protocol itself is a defensible part of the contribution, because none of the related
works (VBQ, SeedLM, Atome) reports total bytes on a physical medium together with clean held-out bpb.

## Minimum experiment

E0 freezes the protocol before any procedural model: dedup and resplit of TinyStories, OOD test generated
and hashed, harness that invokes the C runtime and sums the log-probs, accounting script that reads the
image; then it measures the dense frontier (int8, 4 bits, ternary, shape and vocabulary sweep) and
publishes its bpb-vs-bytes curve and the M5 scores against TinyStories-8M. E1 evaluates the procedural
model with the same harness at equal B_total within 1%, without modifying anything in the protocol after
seeing the results. E2 applies the same entropy coding and the same pruning to all, possibly with a rate
loss in training, and recomputes the curves to test F2. E3 scales the expanded effective parameters and
measures M4 for each point, declaring where F3 fails. E4 writes the real FAT12 image, mounts it on a clean
machine without Python environments and repeats M1, M4 and M5 using only the image files, comparing the
results with those of E1–E3 to rule out that the model evaluated in the lab differs from the one on the
floppy.
