# Experiments roadmap

Owner of the E0–E4 definitions and their completion gates. It does not own results
([evidence](evidence/README.md)) or live state ([STATUS](STATUS.md)). Thesis:
[concept v0.2](concept.md).

Common rules: miniature budgets of 1/16, 1/4 and 1× of 11 Mbit ([ADR 0004](adr/0004-miniature-budgets.md));
in miniature only the coded model bytes count, with embeddings at ~15%; token **and** FLOP parity are
both reported; adversaries and the paired gate are fixed in advance
([ADR 0002](adr/0002-adversary-dense-frontier.md), [ADR 0005](adr/0005-e0v2-protocol.md) §7);
lab practices in [ADR 0003](adr/0003-lab-practices.md). If F1 fires, E2–E4 are _won't run_.

## Sequence

| #   | Step                                                                 | Where           | Cost                  |
| --- | -------------------------------------------------------------------- | --------------- | --------------------- |
| 1   | E0 v2: code and smoke (done); campaign a–e after hardware acceptance | Xbox GPU                   | 55–56 sequential runs; measured costs in campaign reports |
| 2   | Paired σ and adversary freeze (step e)                               | Xbox GPU + host            | 5 seeds |
| 3   | E1 functional qualification, then accepted scientific pilot protocol | CPU oracle; Xbox candidate | Controlled measurements before backend/tokenizer selection ([ADR 0013](adr/0013-e1-functional-qualification.md)) |
| 4   | E1 pilot at 1/16, K=1; preregister the next gate                     | Qualified local backend    | No GPU rental |
| 5   | E1a recursion, E1 at 1/4, E1b trellis/signs                          | Local Xbox/CPU             | Gated by the pilot and accepted protocols |
| 6   | E2 → E3 → E4                                                         | Local Xbox/CPU             | Gated; local judge and 30 blind human reviews |

Scope and execution order: [completion plan](completion-plan.md). Per-trial duration follows from the measured throughput of the bound package
([evidence](evidence/README.md)); it is an estimate, never a duration limit.

## E0 v2 — Accepted numerical choices

The owner accepted this S1–S10 table on 2026-09-30, recorded in
[ADR 0008](adr/0008-e0-numeric-protocol.md); S8 is narrowed by
[ADR 0011](adr/0011-e0-row-scale-selection.md). The protocol is
[ADR 0005](adr/0005-e0v2-protocol.md). Execution runs on the Series S backend of
[ADR 0009](adr/0009-xbox-e0-backend.md) behind the numerical gates of
[ADR 0010](adr/0010-independent-numerical-gates.md); repository boundaries are in
[ADR 0012](adr/0012-repo-boundaries.md).

| #   | Choice                  | Accepted choice |
| --- | ----------------------- | --------------- |
| S1  | Token base T            | 20 × stored parameters; cooldowns ending at T, 2T, 4T |
| S2  | WSD shape               | linear warmup over 2% of T; linear cooldown to zero over 10% of each branch's tokens |
| S3  | Out-of-tolerance repair | a single new attempt per shape and arm: solver re-run with target / (measured coded/nominal); if still out, the run is excluded |
| S4  | Tuning budget           | 6 runs per arm: lr ∈ {1e-3, 3e-3, 1e-2} × a second axis (ternary: Δ ∈ {0.5, 0.7} with wd 0.1; 2-bit: wd ∈ {0, 0.1}) |
| S5  | Seeds                   | at least 3 seeds per comparison; 5 if the mean paired difference is below 2 × gate |
| S6  | Estimated FLOPs         | forward per token = `2 × stored_parameters + 4 × n_layers × (ctx / 2) × d`; training = `3 × forward × tokens`; evaluations excluded and reported separately as wall clock |
| S7  | Evaluation              | sliding window, stride ctx/2, each target byte counted once, last window aligned to the end; the 0x03 separator is a normal target; val on the first MiB, test on the first 2 MiB |
| S8  | Scale policy            | chosen by the step-b A/B between `row16` and `row8log` (ADR 0011) |
| S9  | Zero rows               | exact zero scale, exactly zero reconstruction in every format; `row8log` reserves code 0 for the zero scale |
| S10 | Data                    | exact deduplication (sha1 of the text) is the only current capability; near-duplicate filtering and OOD test remain later requirements |

## E0 v2 — Bench and scalar frontier

Harness `experiments/e0_v2.py` (flags in the [code map](operations/code-map.md)). The pre-v2
E0-lite grid is diagnostic only ([pre-v2](evidence/e0-lite/pre-v2/notes.md)).

- **Data**: TinyStoriesV2-GPT4, exact deduplication, hash split; preparation reproduced from raw
  on 2026-09-30 (`data/tinystories/reproducibility.json`). Near-duplicate filtering and OOD later (S10).
- **Tokenizer**: bytes (V=256) at 1/16 and 1/4. BPE only at 1×.
- **Model**: decoder-only GPT, pre-norm RMSNorm, RoPE, causal attention; ternary or 2-bit core
  with a single scale policy, tied 4-bit embedding, fp16 norms, GELU / ReLU² / SwiGLU MLP,
  optional QK-norm ([ADR 0009](adr/0009-xbox-e0-backend.md)).
- **Shape**: the solver (`floppylm.shapes`) proposes shapes at 99.5–100% of nominal bits; eligibility
  is checked on serialized bytes (`--parity`).
- **Training**: WSD with trunk and cooldowns at T/2T/4T, trunk checkpoints; saturation is
  recorded at 4T ([ADR 0015](adr/0015-e0-fixed-data-frontier.md)).
- **Selection and test**: `--freeze` requires completed, non-smoke, byte-admissible runs with
  equal targets and each candidate within ±1% of that target
  ([ADR 0020](adr/0020-target-window-parity.md)). `--freeze ... --functional` admits
  only smoke runs and marks selection and final result as functional. `--final-test` evaluates a
  selection exactly once. Details in [ADR 0007](adr/0007-e0v2-review-gates.md),
  [ADR 0015](adr/0015-e0-fixed-data-frontier.md).
- **Grid**: children receive the solver's exact shape and the `--tokens`, `--branches`,
  `--val-bytes` limits; one thread per child. The grid is also verified through a real process
  on temporary synthetic data, without launching the campaign.
- **Loaded artifacts**: `unpack` returns an inference model with gradients disabled. `train()` is
  refused; direct changes to config or parameters are detected before re-saving. Resume training
  from a trunk checkpoint.

Campaign steps (executed by `experiments/e0_campaign.py`, see the
[Xbox runbook](operations/xbox-e0.md)):

a. Measure sustained Xbox GPU throughput, transfers and peak memory before scientific runs.
b. Neutral A/B at equal bytes, ternary, 2 seeds: scale policy; GELU vs SwiGLU vs ReLU².
c. Tuning with the S4 budget for ternary and 2-bit.
d. Solver grid with WSD: saturation curve and parity per shape.
e. Paired σ over 5 seeds at the best point → gate; adversary freeze; `notes.md` and `summary.json`.

Completion gates:

1. Run scale/MLP selection, tuning, solver grids and five paired seeds sequentially.
2. Enforce actual-byte gates and rank stability; record saturation; allow only the preregistered byte repair.
3. Freeze ten selected artifact hashes, reserve the final test once, then publish paired
   statistics, costs, exclusions and limitations from the generated campaign report.
4. Review E0's result before specifying and accepting any structural E1 decision.

**Open problem (1/4).** With a byte tokenizer (V=256) the embedding at 1/4 is only 1024·d bits:
the ~15% constraint is met only by wide 2–3 layer models, a degenerate shape. Before E1 at 1/4,
choose between BPE 512 and a relaxed share constraint (explicit later ADR); the 1/16 pilot is
unaffected.

## E1 pilot — Vector vs scalar core at 1/16 (signal on F1, F1-abl)

- K=1, no recursion. 3 seeds, vector rate 0.5 and 0.75 bit/weight, tokens ≈ 20 per stored
  parameter of the largest arm, equal for all.
- **Scalar**: ternary (zero-aware coding), 2-bit. **Vector**: VQ-seed, learned VQ with a shared
  codebook (bytes counted).
- **VQ recipe**: periodic codebook assignment (every N steps, not every step: that would cost as
  much as the forward) with dead-code reseeding, Quant-Noise-style partial quantization
  ([R7](research/07-learned-vq-subbit.md)).
- **F1 signal**: the best vector arm beats the best scalar arm by max(0.02, 2σ).
- **F1-abl signal**: learned VQ vs VQ-seed, codebook included (prior: seed ≥ learned).
- The pilot is not a final verdict ([ADR 0004](adr/0004-miniature-budgets.md)); it gates further
  local Xbox/CPU work. No rented GPU or paid API is authorized.

## E1a — Diversity across iterations (closes v0.1, picks the recursion)

Budget 1/4, core of the pilot's winning arm, same tokens and FLOPs, 3 seeds:

| Arm                | What it adds to pure recursion b0                                          |
| ------------------ | -------------------------------------------------------------------------- |
| b0                 | nothing, shared blocks × K iterations                                      |
| + iter-emb         | one vector per iteration                                                   |
| + IA³              | diagonal scaling per matrix per iteration                                  |
| + LoRA r=1         | rank-1 per matrix per iteration                                            |
| + randn J∈{1,8,64} | fixed random matrices in RAM, learned coefficients `c` (v0.1 without PRNG) |
| ceiling            | K untied blocks, same compute                                              |

If randn ≤ IA³/LoRA r=1 at equal bits, **v0.1 is killed**. If ceiling − b0 < gate, use b0.

## E1 at 1/4 and E1b

- E1 repeated at 1/4 for the pilot's best 2–3 arms, with the E1a recursion: the F1 verdict
  requires the same sign at 1/16 and 1/4.
- E1b: QTIP-style computed trellis (Viterbi quantization in training) and a hybrid of low-rank
  signs (Sign Lock-In) + VQ magnitudes.
- Distillation, if used, only with our own teacher on the same tokenizer, for all arms.

## E2 — Coding and rate loss for all (attacks F2)

- Rate loss `NLL + λ·bits(description)` and rANS on all arms; λ sweep with the same search budget
  per arm.
- **Gate**: the vector advantage survives on coded bytes.
- **MDL control**: compressed corpus + trainer at boot (prequential code), expected to fall outside F3.

## E3 — Full scale and boot cost (attacks F3)

- Budget 1× at convergence, BPE, the whole image counted.
- Boot on the C runtime: index decoding, peak RSS, median tok/s over 5 runs;
  hash of the expanded weights identical across 5 boots.

## E4 — Real image (attacks F4)

_Won't run_ until E1 and E2 pass.

- Static musl binary + tokenizer + description on a 1 474 560 B FAT12 image, mounted and executed
  (the description must fit the data area of [ADR 0001](adr/0001-floppy-budget.md)).
- bpb from the runtime; coherence with a pinned-version LLM judge, 50 prompts × 4 samples,
  TinyStories-8M in the same session, 30 samples in blind human review
  ([R5](research/05-eval-tiny.md)).
- The judge runs locally and must be qualified before use. Actual blind human ratings are
  required; generated placeholders cannot close E4. If a scientific gate fails, publish the
  measured result and stop subsequent phases without creating an alternative scalar-floppy product.
