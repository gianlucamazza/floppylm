# Durable Xbox publication — 2026-10-01

Functional hardware proof of accepted [ADR 0014](../../adr/0014-durable-xbox-publication.md).
No native package change and no scientific campaign restart.

[publication.json](publication.json) binds runner source `25b9cd2` and production Xbox
package 0.1.0.56 / backend source `53ab3c2`.
A tiny d32 synthetic job was interrupted at step 9. The host injected transport loss
before the resume ready marker, after durable journal and candidate job upload.
The old committed binding remained intact; [publication-at-fault.json](publication-at-fault.json)
records the pending candidate. Explicit recovery replayed it, acknowledged the expected hash,
committed the binding and removed the journal.

All three branch files are byte-identical to uninterrupted training; checkpoint step,
stream position, tensors and moments agree. Recovery after completion preserves dispatch
count and branch descriptors instead of requeuing the job. The complete proof reports `ok: true`.
Raw runs: `runs/xbox-publication-20261001-ci36885338811`.

Unit fault injection covers nine publication boundaries; the complete host suite passed
289 tests before this hardware proof. The installed backend artifact is the previously
accepted release, not the separate native audit branch.
