# E1 functional qualification

Measured functional CPU evidence, not scientific results. The owner-approved
qualification is recorded as [ADR 0013](../../adr/0013-e1-functional-qualification.md),
renumbered from the original proposal to avoid the concurrently accepted repository
boundary ADR 0012. The approved numerical decision is unchanged.

See `feasibility.json` for nominal solver shapes, `cpu-profile-summary.json` (with
[cpu-profile-notes.md](cpu-profile-notes.md)) for the scalar diagnostic and `functional-summary.json` for vector/BPE qualification.
All reports bind input and source hashes; no validation/test bytes were opened
and no console job was submitted.

The final scalar CPU profile reproduced all three canonical branches across three attempts, with initialization, WSD forks and serialization included. Raw repetitions are in cpu-profile-summary.json. These short measurements do not select the scientific E1 backend. Three profiler tests passed; Ruff checks passed.

## Results

- Byte BPE trained on the first 2 MiB of the frozen train split reached V=512.
  Its complete canonical configuration/merge table is 2,566 bytes, saved as
  `bpe512.json`. The prefix becomes 1,213,820 tokens (1.7277 bytes/token).
  Prefix and arbitrary-byte probes decode exactly. This is compression evidence,
  not an LM quality comparison or a tokenizer selection.
- Sixteen vector probes cover fixed/learned books, G=8/16, rate=0.5/0.75 and
  row16/row8log. Shared books are counted once for two named matrices. Headers,
  scales, padded indices and actual coded symbol streams are counted exactly.
  Artifact decodes match the direct oracle and zero rows reconstruct exactly.
- A learned 4096x16 fp16 book uses 131,072 entry bytes plus a 16-byte header:
  it alone exceeds the 85,937.5-byte 1/16 model budget. Other fixture sizes do
  not establish full-model byte feasibility.
- Twelve partial-quantization/snapping canaries (six per arm) each ran 257 steps
  twice, exercising every cadence at least once. Gradients remained finite,
  learned books changed, fixed books remained fixed, and repeated master weights,
  fully quantized artifact hashes and reconstruction losses matched exactly.
  These 4x16/G8/r0.5/row16 canaries do not qualify training at other book sizes.
- PCG generation matches an independent compiled C recurrence; nearest assignment
  and book gradients have independent explicit test oracles. The full suite passed
  175 tests, with four native-backend tests skipped because its binary is absent
  in this isolated worktree. Two additional input-binding rejection tests passed.
  Ruff and diff whitespace checks pass.

Raw artifacts live in ignored `runs/e1-functional-20261001-adr0013/` and can be
reproduced with the committed runner and frozen train hash:

```bash
/home/gianluca/.local/bin/bg python scripts/e1_qualify.py \
  --train data/tinystories/train.bin \
  --train-sha256 8745f0d0f0c2ede79305e35393f90b35ff15c91fa1d85abed2acafdf4046e092 \
  --out runs/e1-functional-new
```

## Remaining gates

Vector/BPE integration into a scientific model is unimplemented. Full-model byte
accounting, persistent assignments, checkpoint/resume, dead-code treatment,
tokenizer/context fairness, actual backend parity and equal tuning/sample budgets
must be fixed by a later accepted scientific protocol. Xbox vector performance
has not been measured; the console is reserved for E0. E1 science remains gated
by E0 completion. No F1/F2 verdict follows from these probes.
