# FloppyLM harness audit — 2026-10-01

Scope: protected final evaluation and frozen scientific recovery. Changes are published after
the dashboard release, separately from its hardware package.

| Finding | Reproduction | Correction |
| --- | --- | --- |
| P1: final-test reservation and protected corpus load precede artifact verification | Tampered selected bytes caused `data_mod.load(..., "test")` before the hash refusal; a later invalid artifact could follow an earlier model evaluation | Preflight every hash, declared byte size and FLP2 format; keep validated models before reserving or loading test data |
| P1: scientific final evaluation does not bind the prepared test corpus to the frozen trials | The final-test path omitted comparison with trial `data_sha256.test` | Require one consistent frozen test hash and verify the prepared corpus before reservation |
| P1: incomplete scientific Xbox recovery can execute modified runner sources | The manifest recorded source hashes but `cmd_resume` did not compare them | Refuse source drift before training; completed read-only recovery remains idempotent |

Verification: 280 tests pass with the corrected native reference binary, including negative
probes that assert no protected-data load, no earlier-model evaluation, no reservation after
invalid input, and refusal of changed sources. Ruff passes. These are functional invariants,
not a scientific final-test result or a claim about language-model quality.

The transport crash window has a separate owner-approved decision,
ADR 0014 (durable Xbox publication), and separate recovery implementation.
The E0 saturation proposal remains an owner decision; this audit does not restart the campaign
or alter historical evidence.

Later note (2026-10-01): the proposal is accepted as
[ADR 0015](../../adr/0015-e0-fixed-data-frontier.md) (option B). This record is unchanged.
