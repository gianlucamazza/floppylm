# E1 qualification preparation

Proposed candidates and measured nominal solver feasibility, not scientific results.
See feasibility.json for exact shapes and learned-book costs.
ADR 0012 requires acceptance before vector/BPE implementation.
CPU profiling uses the existing scalar oracle and hash-bound synthetic benchmark input; no validation or test opened.

The final scalar CPU profile reproduced all three canonical branches across three attempts, with initialization, WSD forks and serialization included. Raw repetitions are in cpu-profile-summary.json. These short measurements do not select the scientific E1 backend. Three profiler tests passed; Ruff checks passed.

The prototype proposal is in ../../e1-qualification-proposal.md; no vector or BPE structural code has been implemented before acceptance.
