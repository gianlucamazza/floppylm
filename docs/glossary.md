# Glossary

One line per term; the owner holds the definition of record.

| Term                             | In one line                                                                    | Owner                                                                     |
| -------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| `image_bytes` | Bytes allocated on the FAT12 image, everything included                        | [ADR 0003](adr/0003-lab-practices.md) §1, [ADR 0001](adr/0001-floppy-budget.md) |
| Sub-bit regime                   | Less than 1 stored bit per unique (or effective) weight                        | [concept](concept.md)                                                     |
| Effective parameters | Parameters of the model expanded in RAM at boot, recursion included            | this glossary |
| Core                             | Transformer block weights, excluding embedding and norms                       | [concept](concept.md)                                                     |
| Vector core                      | Core written as indices into a code over blocks of `v` weights                 | [concept](concept.md)                                                     |
| VQ-seed / trellis / learned VQ   | The three competing core decoders                                              | [concept](concept.md), [R7](research/07-learned-vq-subbit.md)             |
| Coded bytes                      | Bytes after entropy coding, the basis of every comparison                      | [concept](concept.md) P3                                                  |
| Miniature budget                 | 1/16 and 1/4 of 11 Mbit, compared at equal tokens                              | [ADR 0004](adr/0004-miniature-budgets.md), [ADR 0015](adr/0015-e0-fixed-data-frontier.md) |
| Scalar frontier                  | Best dense low-bit (ternary/2-bit) model after shape search                                     | [ADR 0002](adr/0002-adversary-dense-frontier.md)                          |
| Rate loss / MDL                  | `NLL + λ·bits(description)`                                                    | [R3](research/03-mdl-compression.md)                                      |
| bpb                              | Bits per byte of held-out text, from the C runtime                             | [R5](research/05-eval-tiny.md)                                            |
| Boot                             | Mount → decode/expand → first token                                            | [ADR 0001](adr/0001-floppy-budget.md)                                     |
| Trunk / cooldown                 | Constant-LR training; branches decaying to LR 0 and ending at T, 2T, 4T        | [ADR 0005](adr/0005-e0v2-protocol.md)                                     |
| Saturated                        | \|bpb(4T) − bpb(2T)\| < 0.01 on val; recorded, not an eligibility gate         | [ADR 0005](adr/0005-e0v2-protocol.md) §4, [ADR 0015](adr/0015-e0-fixed-data-frontier.md) |
| Byte parity                      | Each within ±1% of target and max/min − 1 ≤ 1% on serialized bytes             | [ADR 0005](adr/0005-e0v2-protocol.md)                                     |
| Paired σ                         | Standard deviation of the differences between two conditions on the same seeds | [ADR 0005](adr/0005-e0v2-protocol.md)                                     |
| Frozen selection                 | Artifacts chosen on val, fixed by hash before the test                         | [ADR 0005](adr/0005-e0v2-protocol.md)                                     |
| S1–S10 | The accepted E0 numerical choices | [roadmap](roadmap.md#e0-v2--accepted-numerical-choices), [ADR 0008](adr/0008-e0-numeric-protocol.md) |
| FLP2                             | The only blob format; FLP1 (pre-v2) is rejected                                | [ADR 0006](adr/0006-flp2-only.md)                                         |
| `row16` / `row8log` / `tensor16` | Scale policies; scientific E0 uses only the first two                          | [ADR 0011](adr/0011-e0-row-scale-selection.md)                            |
| Python oracle                    | The host PyTorch implementation every native result is checked against         | [ADR 0009](adr/0009-xbox-e0-backend.md)                                   |
| Xbox backend / package           | The DX12/UWP E0 trainer; a package is one signed, installed build              | [ADR 0009](adr/0009-xbox-e0-backend.md), [runbook](operations/xbox-e0.md) |
| E0.1                             | Backend generation with GPU-resident tensors, bit-identical to its predecessor | [evidence](evidence/xbox-e0-20261001-e01/notes.md)                        |
| Acceptance                       | Hardware proof (operations, fixtures, optimizer, resume) a campaign binds to   | [ADR 0010](adr/0010-independent-numerical-gates.md)                       |
| Campaign                         | Frozen sequential E0 execution (sources, recipes, seeds) with one worker       | [runbook](operations/xbox-e0.md)                                          |
| Recovery                         | Explicit operator restart of a missing process, then `--recover`: reconnect or resume a verified checkpoint, never retrain | [runbook](operations/xbox-e0.md)                                          |
