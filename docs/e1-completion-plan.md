# FloppyLM completion ledger

Owner-approved scope (2026-10-01): E0–E4 with gates, local Xbox/CPU, no GPU rental
or paid judge. A scientifically negative result closes the research with measured
frontiers; it does not trigger an alternative scalar-floppy product.

| Stage | Required result | Current status |
| --- | --- | --- |
| E0 | Complete scalar campaign, paired statistics, one reserved final test | E0.1 running; earlier 0.1.0.24 campaign intentionally stopped |
| E1 qualification | Vector/BPE oracles, storage feasibility, CPU profile, later Xbox canary | [ADR 0012 proposal](e1-qualification-proposal.md); CPU/scalar diagnostics measured |
| E1 protocol | Accepted format, tokenizer/context, recipes, byte parity, backend and reservation | Await qualification results; no scientific E1 authorization yet |
| E1 pilot | 1/16 scalar/vector comparison with paired seeds | Gated by E0 and E1 protocol |
| E1a/E1/E1b | Recursion selection, 1/4 confirmation, trellis/sign hybrid | Gated by pilot and respective preregistered protocols |
| E2 | Matched coding/rate-loss comparison and F2 verdict | Gated by F1 |
| E3 | Full scale plus deterministic static C runtime and measured F3 | Gated by F1/F2 and local hardware feasibility |
| E4 | FAT12 artifact, qualified local judge, reference and 30 blind human reviews | Gated by F3; no completion without actual ratings |

## Isolation and rollout

Development is in `/tmp/floppylm-e1-qualification`, branch
`research/e1-qualification`. Preserve its committed branch before cleanup; `/tmp`
is not permanent artifact storage. The active campaign checkout is
`/home/gianluca/Workspace/experiments/floppy_4mb`. Do not merge new `src/floppylm`
or `experiments` files there while its worker is bound to a frozen file set.

Use existing `bg` routing for CPU-heavy jobs. No parallel GPU job is submitted
during E0. The current operating guide and campaign manifest own live state;
record a timestamped observation rather than assuming the old package remains
installed. Never recover a deliberately retired campaign into a replacement package.

## Decisions already fixed

- Backend/tokenizer selection uses controlled qualification, then an accepted ADR.
- The original test split is excluded from prototype construction and selection.
- CPU is the independent numerical oracle even if Xbox becomes the scientific backend.
- Round-trip byte fidelity and exact artifact accounting are mandatory.
- Operational failure, unsaturated training and invalid byte parity do not prove
  the vector hypothesis false; preserve and diagnose them separately.
- New structural choices remain proposals until accepted; accepted ADRs are not rewritten.
