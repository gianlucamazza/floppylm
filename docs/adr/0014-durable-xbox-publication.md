# ADR 0014: Durable Xbox job publication

## Status

`accepted` — 2026-10-01; explicitly approved by the owner. Applies to companion submit/resume and recovery only.

## Context

`Portal.resume` replaces `submitted.json` before uploading the final `.ready` marker.
A transport failure at that boundary leaves a new local submission hash against an old
remote status; `recover` then refuses the mismatch permanently. Simply moving the local
write after the remote upload reverses the crash window. A two-party file handoff cannot
be one atomic rename. Missing or stale remote statuses also wait indefinitely today.

## Decision

- Keep the native job/ready/claimed protocol and its schemas unchanged. No implicit
  retraining, checkpoint migration, package switch or numerical change.
- Before remote side effects, atomically write a local `publication.json` journal containing
  the previous committed binding (if any), candidate job/payload hash/package, and kind
  (`submit` or `resume`). Preserve `submitted.json` as the committed binding until the
  console acknowledges the candidate hash in its status.
- On startup/recovery, reconcile a pending journal against the same hardware package,
  recipe/assets and remote status. A candidate-hash acknowledgment commits the candidate
  binding. Otherwise replay the identical candidate upload and ready marker only when
  the old execution is not running. An unrelated hash or failed old execution is an error.
- A replay is idempotent: a matching acknowledged execution is reattached/retrieved and
  never requeued. Resume keeps the exact checkpoint and the execution-segment record.
- Bound the initial acknowledgment/status-mismatch wait to 300 seconds and log the
  expected/observed identity and phase. Once acknowledged, report ten minutes without
  progress as a diagnostic event; do not cancel or retrain valid GPU work automatically.
  Persistent missing/mismatched status raises with the journal intact for explicit recovery.
- Failure injection before/after journal write, job upload, cancel removal, ready upload,
  acknowledgment and binding commit must preserve recovery or a specific safe refusal.

## Consequences

Local publication becomes a recoverable state machine; backend bytes and scientific gates
stay fixed. Journal reconciliation is mandatory in both fresh and resumed paths. Hardware
recovery acceptance must include an interrupted publication followed by successful exact
resume. Historical evidence and frozen scientific campaigns remain untouched.

## Alternatives considered

- Write `submitted.json` after `.ready`: loses the binding if the host dies after dispatch.
- Retry `.ready` blindly: can replay an acknowledged job and corrupt its evidence.
- Accept an arbitrary remote hash: breaks the submission provenance boundary.
