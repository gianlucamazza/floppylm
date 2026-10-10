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
   stay proposed in [the 1/16 pilot proposal](adr/proposals/e1-1-16-pilot.md)
   and are not accepted. A later ADR still has to copy both stored decisions
   and that selection hash, replace the proposal's reciprocal byte check with
   the ADR 0020 window, and fix the byte layout.
3. The console is free. No Xbox vector executor exists in this repository or in
   the accepted trainer. `src/floppylm/vq.py` remains the CPU fixture oracle from
   [ADR 0013](adr/0013-e1-functional-qualification.md). Qualification has not
   started. When an executor exists, the tasks are: give it the inputs of a
   published CPU vector fixture; require identical artifact bytes and a decode
   that matches that oracle; record the comparison under `docs/evidence`. A
   scalar throughput measurement does not qualify it. Do not build that
   executor under the unaccepted 1/16 proposal.
4. Acceptance of the 1/16 pilot is a separate explicit step
   ([issue #25](https://github.com/gianlucamazza/floppylm/issues/25)). It is not
   taken here. Draft [PR #2](https://github.com/gianlucamazza/floppylm/pull/2)
   was closed on 2026-10-10 without merge.
   [Issue #26](https://github.com/gianlucamazza/floppylm/issues/26) is closed:
   the pages left on `docs/excellence-research-20261001` are an audit dated
   2026-10-01. They are not the live protocol and are not merged. Once a scientific protocol is
   accepted, integrate the model/format and run the paired 1/16 pilot; proceed
   through E1a/E1/E1b and E2–E4 only on passing gates. Keep local-judge
   qualification and actual 30 blind human ratings explicit at E4.

The `c58a86` source freeze was released by that stop. [PR #22](https://github.com/gianlucamazza/floppylm/pull/22)
merged the host init-pack ([ADR 0019](adr/0019-host-init-pack.md)) for a future campaign.
It does not apply to the cells already measured. No full-project completion claim is justified yet.
