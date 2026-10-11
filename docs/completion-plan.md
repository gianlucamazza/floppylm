# FloppyLM completion plan

Owner of the approved completion scope and execution order. Per-stage live state is in
[STATUS](STATUS.md); stage definitions and gates are in the [roadmap](roadmap.md).

Owner-approved scope (2026-10-01): E0–E4 with gates, local Xbox/CPU, no GPU rental
or paid judge. A scientifically negative result closes the research with measured
frontiers; it does not trigger an alternative scalar-floppy product.

| Stage            | Required result                                                                                                               |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| E0               | Complete scalar campaign, paired statistics, one reserved final test                                                          |
| E1 qualification | Vector/BPE oracles, storage feasibility, CPU profile, later Xbox canary ([ADR 0013](adr/0013-e1-functional-qualification.md)) |
| E1 protocol      | Accepted format, tokenizer/context, recipes, byte parity, backend and reservation                                             |
| E1 pilot         | 1/16 scalar/vector comparison with paired seeds                                                                               |
| E1a/E1/E1b       | Recursion selection, 1/4 confirmation, trellis/sign hybrid                                                                    |
| E2               | Matched coding/rate-loss comparison and F2 verdict                                                                            |
| E3               | Full scale plus deterministic static C runtime and measured F3                                                                |
| E4               | FAT12 artifact, qualified local judge, reference and 30 blind human reviews                                                   |

## Isolation and rollout

E1 qualification code is on `main`: `src/floppylm/{bpe,vq}.py`, `scripts/e1_*.py` and their tests
([code map](operations/code-map.md)). While a campaign runs, its frozen file set
(`runlog.source_files`) covers every module under `src/` and `experiments/`, so new modules are
merged only between campaigns.

Use the existing CPU job routing ([stack](stack.md)) for CPU-heavy jobs. No parallel GPU job is
submitted during E0. [STATUS](STATUS.md) and the campaign manifest own live state; record a
timestamped observation rather than assuming the old package remains installed. Never recover a
deliberately retired campaign into a replacement package.

## Decisions already fixed

- Backend/tokenizer selection uses controlled qualification, then an accepted ADR.
- The original test split is excluded from prototype construction and selection.
- CPU is the independent numerical oracle even if Xbox becomes the scientific backend.
- Round-trip byte fidelity and exact artifact accounting are mandatory.
- Operational failure, unsaturated training and invalid byte parity do not prove
  the vector hypothesis false; preserve and diagnose them separately.
- New structural choices remain proposals until accepted; accepted ADRs are not rewritten.

## Completed qualification and next execution gates

[CPU evidence](evidence/e1-qualification-20261001/notes.md) includes BPE512 trained
on the frozen train prefix, 16 vector storage/reconstruction configurations,
12 deterministic QAT/snapping recipes, independent PCG/assignment/gradient oracles
and scalar CPU profiling. No validation/test split or console job was used.
The accepted record is administratively renumbered 0013 because concurrent main
commit `8b76068` assigned 0012 to repository boundaries; the decision is unchanged.

Continue in this order:

1. Campaign `e0-20261009T150330Z-87686a` stopped at 2026-10-09T15:12:23Z in
   `paired-seeds` on package 0.1.0.105. Run `87686a-000` failed on the console
   at trunk step 64 with `JSON write failed` and wrote no branch. Do not recover
   it. Cell `031` of `766d4b` failed earlier with the same device message and is
   not a result. The stored decisions remain ternary `d` 80, 4 layers, `d_ff` 262
   and 2-bit nominal `d_ff` 193 (trained cell `027` submitted `d_ff` 205,
   1.4914/1.3663/1.2766). The scalar recipe is not named. `766d4b` and `4236fd`
   stay stopped. [ADR 0022](adr/0022-paired-campaign-on-109.md) opened
   `e0-20261009T174028Z-94847b` on package 0.1.0.109. It completed at
   2026-10-10T10:02:53Z. Ten paired cells are eligible and the ten hashes are
   frozen. Byte parity and rank stability passed. The final test records
   ternary minus 2-bit −0.023838 bpb against frozen gate 0.026322, inside the
   gate. The report keeps both stored arms. The campaign does not
   resume `87686a`.
2. The completed E0 report was reviewed on 2026-10-10
   ([gate 4](evidence/e0-review-20261010-94847b/notes.md)). Both stored arms
   remain. The selection hash is
   `de80fff08e750702784e6efbcb583ca86de566965207212c1c6531822a05bbe4`.
   The rules that do not depend on that report — books, assignment,
   dead codes, checkpoints, token parity, F1, and what the container must count —
   are recorded from [the 1/16 pilot proposal](adr/proposals/e1-1-16-pilot.md).
   That proposal copies both stored decisions and
   the selection hash, and its equal-byte rule is the ADR 0020 window. The
   scientific file is FLP2. Decision 14 specifies the byte order: one `VQB1`
   book in the shared section, `core_fmt` `vq` on a vector arm, and the
   existing per-tensor framing. `VQF1` stays the functional fixture.
   On 2026-10-11 the E0 experiment series stops. No further scalar campaign
   is opened to force one named format. The same day the proposal is accepted
   as [ADR 0023](adr/0023-e1-1-16-pilot.md). The pilot does not start with
   that acceptance.
3. The console is free. No Xbox vector executor exists in this repository or in
   the accepted trainer. `src/floppylm/vq.py` remains the CPU fixture oracle from
   [ADR 0013](adr/0013-e1-functional-qualification.md). CPU functional
   qualification is measured. Xbox vector qualification has not started.
   When an executor exists, the tasks are: give it the inputs of a
   published CPU vector fixture; require identical artifact bytes and a decode
   that matches that oracle; record the comparison under `docs/evidence`. A
   scalar throughput measurement does not qualify it. ADR 0023 keeps the pilot
   on CPU until that match is recorded. Building the executor is not the next
   task.
4. Acceptance of the 1/16 pilot is recorded on 2026-10-11 as
   [ADR 0023](adr/0023-e1-1-16-pilot.md)
   ([issue #25](https://github.com/gianlucamazza/floppylm/issues/25)). Draft
   [PR #2](https://github.com/gianlucamazza/floppylm/pull/2) stays closed and
   unmerged.
   [Issue #26](https://github.com/gianlucamazza/floppylm/issues/26) is closed:
   the pages left on `docs/excellence-research-20261001` are an audit dated
   2026-10-01. They are not the live protocol and are not merged. The host
   FLP2 layout is on main (`b362991`): one `VQB1` book in the shared section.
   The host trainer is `e9e7ef8`
   ([python run 38095852624](https://github.com/gianlucamazza/floppylm/actions/runs/38095852624)).
   The layer map is [architecture](architecture.md) (`e4bc41d`).
   The host plan is `src/floppylm/e1_plan.py`. It materializes the specified
   scalar arms, the four G=8 books, and the
   [ADR 0024](adr/0024-e1-vector-shape.md) shape rule. Seed 0 of the fixed
   rate-0.5 book is closed at `d` 80, 12 layers, `d_ff` 247, 85934 bytes.
   The learned rate-0.5 book is closed at `d` 256, 1 layer, `d_ff` 801,
   85935 bytes. The fixed rate-0.75 book is closed at `d` 80, 8 layers,
   `d_ff` 258, 85938 bytes. One book remains open, so the pilot token count is unnamed. The trainer applies
   ADR 0023 decisions 7–9 on CPU. Assignment is
   every 64 steps at probability 0.1. A dead learned entry is reseeded from
   that arm's PCG32 stream and logged. A fixed book logs the dead entry and
   keeps the seed. Resume continues the master weights, indices, scales,
   book, and optimizer moments. The cooldown artifact is that quantized
   container. The paired 1/16 pilot has not started. No console job is
   authorized. Proceed through E1a/E1/E1b and E2–E4 only on passing gates.
   Keep local-judge qualification and actual 30 blind human ratings explicit
   at E4.

The `c58a86` source freeze was released by that stop. [PR #22](https://github.com/gianlucamazza/floppylm/pull/22)
merged the host init-pack ([ADR 0019](adr/0019-host-init-pack.md)) for a future campaign.
It does not apply to the cells already measured. No full-project completion claim is justified yet.

## Completion task map (2026-10-11)

This section owns the forward order. It does not amend
[ADR 0023](adr/0023-e1-1-16-pilot.md) or
[ADR 0024](adr/0024-e1-vector-shape.md). Live rows stay in
[STATUS](STATUS.md). A yes on one row does not authorize the next row.
The pilot has not started. No console job is authorized.

The approved scope is the E0–E4 ladder, local Xbox/CPU only, with no rented
GPU. The ladder is not walked by default. The research is complete when F1,
F2, F3, or F4 fires and the measurement is published; later rows do not start,
and no alternative scalar-floppy product is opened. The product is complete
only when F1 and F2 do not fire and E4 closes. E0 is measured. F1 and F2 are
not decided. A smoke, a placeholder, or an open shape closes neither end.

| Id | Task | Depends on | Done when | Yes |
| --- | --- | --- | --- | --- |
| A0 | Finish the four seed-0 shapes, or publish the stop | ADR 0024. Three books are closed; the learned rate-0.75 book is open | Every G=8 book has an admissible init pack, or one book has none and the pilot stays stopped. T is named only when four shapes exist | Already given |
| A1 | CPU pilot driver | A0 with four shapes | The driver reads the preregistered shapes, seeds 0/1/2, one shared T, cooldowns at T, 2T and 4T, one S3, one freeze, and one `--final-test`. A synthetic smoke passes and is not a result | Separate yes after the shapes are written |
| A2 | Eighteen runs | A1 | Six recipes times three seeds, one job at a time, on the lab machine. Each closed cell has `notes.md` and `summary.json` | Separate yes after A1 |
| A3 | Pilot signal | A2, eligible validation repairs only | ±1% parity, rank at T/2T/4T, saturation recorded and not used as a gate, F1, F1-abl, costs, exclusions, fill, frozen hashes, one final test. The signal is not the F1 verdict | Included in the A2 yes |
| B0 | 1/4 tokenizer ADR | A favorable A3 signal | Accepted choice of BPE 512 or a relaxed embedding share. The 1/16 pilot is not recomputed | Yes with that ADR |
| B1 | E1a | B0 | Budget 1/4, the winning arm's core, the same tokens and FLOPs, three seeds: b0, iter-emb, IA³, LoRA r=1, randn J in {1, 8, 64}, and a ceiling of K untied blocks. randn at or below IA³ or LoRA at equal bits kills v0.1. ceiling − b0 below the gate selects b0 | Yes after B0 |
| B2 | E1 at 1/4 | B1 | The pilot's best two or three arms, with the chosen recursion. The sign is published. A disagreement with 1/16 leaves F1 undecided and stops the ladder | Yes after B1 |
| B3 | E1b | B2 with the same favorable sign | Its own ADR, then a QTIP-style computed trellis and low-rank signs plus VQ magnitudes | Yes for the ADR, then yes for the runs |
| C0 | E2 | F1 did not fire at 1/16 and at 1/4 | An ADR for `NLL + λ·bits(description)` and rANS on every arm, with the same λ search budget per arm. The MDL control is recorded and not chased. F2 is decided | Yes for the ADR, then yes for the runs |
| D0 | E3 | F2 did not fire | Budget 1×, BPE, the whole image counted, a static C runtime. Boot records index decode, peak RSS, median tok/s over five runs, and an expanded-weight hash identical across five boots. F3 fires above 60 s, above 1 GB, or below 5 tok/s | Yes for the ADR, then yes for the measurement |
| E0d | S10 | Before an E4 claim, not before the pilot | Near-duplicate filtering and an OOD test, beyond the sha1 dedup already done | Yes after D0 does not fire F3 |
| E1j | Local judge | R5, before E4 | A qualification protocol. Fifty prompts times four samples, with TinyStories-8M in the same session. Generated output does not qualify the judge | Yes for the protocol |
| E2i | E4 | E1j and E0d | A 1 474 560-byte FAT12 image, mounted and executed, plus 30 blind human ratings. F4 fires when coherence is not non-inferior to TinyStories-8M (margin 0.5) or grammar and coherence are below 6 and 5 | Yes for the image, after the judge |
| H0 | ADR 0012 pin | Between campaigns, never during a source freeze | xbox-gpu-training tests schema fields added after commit `3e5ab3c`, or a note records that the pin stays | Separate yes. Not a scientific gate |

A1 reads shapes that are already written. Seeds 1 and 2 may move only `d_ff`,
by the same closest-file rule inside the same interval. That move is the
[ADR 0019](adr/0019-host-init-pack.md) init pack. It does not change G, rate,
or book length. The driver is not an Xbox executor and not an Odroid unit.

A2 runs one job at a time. The ADR 0004 estimate of 0.5–1 h is the scalar
1/16 figure and is not a limit. A3 uses the ADR 0023 F1 rule:
`max(0.02, 2σ)`, and lower at T and at 2T as well. F1-abl is learned minus
seed at the same G and rate, book included. The prior is that the seed is at
least as good. The F1 verdict exists only when the 1/4 sign agrees.

If A0 publishes a stop, A1 through E2i do not start. If A3 fires F1 at 1/16,
B0 through E2i do not start.

An Xbox vector executor may replace the CPU only after it matches `vq.py` on
identical inputs and identical artifact bytes. A scalar throughput number does
not qualify it, and the CPU thesis does not need it. The C runtime, the FAT12
image, and the tokenizer image wait for their own yes. Surveys 01–06 stay
closed. The F0 check stays continuous and does not block A0.
