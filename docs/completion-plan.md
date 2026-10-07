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

1. The E0 campaign named in [STATUS](STATUS.md) is `e0-20261004T103838Z-c58a86`. It stopped
   on 2026-10-07 during ternary selection, with no ternary winner. Scale, MLP and ternary
   tuning are closed. The ternary grid was measured and the set was refused. 2-bit tuning,
   the 2-bit grid, paired seeds and the reserved final test remain for a new campaign.
   `4236fd` is an earlier stopped campaign. No campaign is running. Launch of any new
   campaign is a separate, explicit step.
2. Review the completed E0 report (roadmap gate 4) before accepting a scientific
   E1 ADR. The rules that do not depend on that report — books, assignment,
   dead codes, checkpoints, token parity, F1, and what the container must count —
   are proposed in [the 1/16 pilot proposal](adr/proposals/e1-1-16-pilot.md) and
   are not accepted. The ADR still has to copy the scalar recipe and the
   selection hash from the E0 report, and to fix the byte layout.
3. After E0 releases the console, qualify any Xbox vector executor against the CPU
   oracle with identical inputs and artifact bytes. Choose backend/tokenizer only
   from the controlled qualification required by the owner. A scalar throughput
   measurement does not qualify a vector backend.
4. Once the scientific protocol is accepted, integrate the model/format and run
   the paired 1/16 pilot; proceed through E1a/E1/E1b and E2–E4 only on passing gates.
   Keep local-judge qualification and actual 30 blind human ratings explicit at E4.

The `c58a86` source freeze was released by that stop. [PR #22](https://github.com/gianlucamazza/floppylm/pull/22)
merged the host init-pack ([ADR 0019](adr/0019-host-init-pack.md)) for a future campaign.
It does not apply to the cells already measured. No full-project completion claim is justified yet.
