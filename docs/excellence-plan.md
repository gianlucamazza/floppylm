# Excellence and research plan

Audit date: 2026-10-01. Inspected baseline: `001993e62d517642a30ba30617b8999c20756cdc`.
This is an audit snapshot and execution backlog, not an amendment to the scientific protocol.
Live state belongs to [STATUS](STATUS.md); experimental authority remains the [roadmap](roadmap.md).

## Objective

Make the project understandable, falsifiable and reproducible while reducing the work needed to
answer whether sub-bit vector cores improve held-out language quality at equal serialized bytes.
A measured negative answer is a valid research outcome. More reconstructed weights alone are not success.

## Findings and acceptance criteria

P0 blocks a scientific verdict; P1 can change interpretation; P2 improves reproducibility;
P3 improves presentation. These are review priorities, not confirmed implementation defects.

| ID | Priority | Evidence / finding | Next action | Acceptance criterion |
| --- | --- | --- | --- | --- |
| X01 | P0 | E0 eligibility rejects unsaturated runs in `experiments/e0_campaign.py`; the saturation proposal documents the stopped campaign | Decide the existing [proposal](adr/proposals/e0-saturation-proposal.md) before a new preregistration | The estimand, token schedule and termination rule agree in ADR, harness and frozen config; old runs remain diagnostic |
| X02 | P1 | `concept.md` mentions a bootable artifact in its gap claim; ADR 0001 explicitly specifies a data floppy | Correct that factual inconsistency | Public explanations consistently describe a mounted data disk and a Linux host |
| X03 | P1 | R7 says a counter-example does not exist, which a bounded literature search cannot establish | Qualify the novelty wording and record search coverage in R8 | Novelty is a candidate comparative contribution; no universal absence claim |
| X04 | P1 | `parity.paired_sigma` returns sample SD; campaign gate is `max(0.02, 2*sd)` | Report the gate as an engineering effect threshold; plan uncertainty separately | No conversion of 2σ into a confidence level; seed-level differences and n published; vector/scalar uncertainty estimated for that pair |
| X05 | P1 | The roadmap's 1/4 embedding-share constraint restricts shapes with V=256 | Compare BPE 512 versus a relaxed share in a separate proposal | Candidate grid sizes, tokenizer bytes and bpb denominator documented before selecting a policy |
| X06 | P1 | Roadmap S10 supports exact dedup only; evaluation uses fixed prefixes | Quantify near-duplicate exposure and prefix representativeness before broader claims | Contamination report, split hashes and document-level evaluation summary; no silent re-splitting of an existing campaign |
| X07 | P1 | E1 pilot compares at equal tokens; larger reconstructed cores can require more FLOPs | Preregister a second matched-compute view and assignment cost accounting | Equal-token and equal-compute claims are distinct; snapping, code search, tuning and host work included in costs |
| X08 | P1 | `vq.py` is a standalone VQ fixture oracle, not an integrated scientific LM or FLP2 vector extension | Specify a model/codec integration gate before E1 science | Packed/reloaded complete LM evaluated; scalar and vector artifacts use declared envelopes; no fixture qualification promoted to quality evidence |
| X09 | P2 | Five exchange schemas exist; remaining contracts are listed in STATUS | Complete contract inventory, pinned consumer revision and independent backend checks | Producer/consumer tests cover checkpoint, optimizer, fixtures and failures; ownership follows ADR 0012 |
| X10 | P2 | No `.github/workflows` in inspected tree; local test requirements exist | Add host CI in a separate implementation change | Clean Python 3.12 install runs pytest, ruff and schema fixtures without console credentials or corpus downloads |
| X11 | P3 | README exposes technical rates and gates before explaining reconstruction | Add plain-language intro and architecture reading path | Reader can identify constraint, hypothesis, comparison and current evidence boundary in one minute |

## Execution order

1. Complete the source-backed research pass R8–R12 and the claim matrix below.
2. Resolve X01 with a concrete protocol proposal. Recommendation: consider option B for a
   **fixed-data frontier**, retaining saturation diagnostics; it does not establish a converged frontier.
   Rank stability at T/2T/4T does not prove rankings remain stable beyond 4T. A later convergence
   claim would need longer confirmatory runs. No selection gate is weakened by this document.
3. Resolve X04–X08 in an E1 preregistration before committing training time. Do not infer
   vector/scalar variance from scalar/scalar variance alone.
4. Finish X09–X10 with host checks and independent native acceptance; no console deployment here.
5. Execute the qualified pilot only after the upstream gates. Publish exclusions and null results.
6. Populate the [paper scaffold](paper-outline.md) from frozen evidence, then review full-scale costs.

## Claim → evidence → counter-evidence → experiment

| Claim | Evidence available | Counter-evidence / uncertainty | Decisive experiment |
| --- | --- | --- | --- |
| A compact description can reconstruct more numerical weights | Scalar codecs and standalone VQ fixture accounting | Reconstructed weight count is not independent learned information | Full packed/reloaded LM and held-out bpb |
| Vector coding beats scalar at equal bytes | Hypothesis; CPU qualification is functional evidence only | BTC-LLM/QTIP are not evidence of tiny from-scratch superiority | E1 with frozen adversaries, seeds, byte parity and costs |
| Learning a codebook is worth its storage | Learned-book serialization in `vq.py` | Fixed/computed codes and codebook overhead provide a strong adversary | Learned versus fixed at equal total bytes, all shared bytes counted |
| Recursion improves quality per byte | Relevant external recursive-transformer studies | Added depth increases compute; external scales and data differ | E1a, same recursion controls and explicit compute accounting |
| A complete model fits the physical disk | Budget specification in ADR 0001 | Runtime and whole image have not been established by a specification | E3/E4 on final static runtime and cluster-rounded files |

## Deliverables and boundaries

This change delivers narrative, an architecture map, five bounded research briefs and a paper
scaffold. It corrects two unsupported/documentation claims. It does not change accepted ADRs,
training sources, schemas, frozen evidence or live state. Research briefs distinguish reviewed
abstracts/central claims from full-text replication; they do not certify a complete literature review.

Verification: inspect relative Markdown links and diff whitespace. Python scientific tests require
PyTorch and pytest, absent in this execution environment; no training or numerical result is claimed.
