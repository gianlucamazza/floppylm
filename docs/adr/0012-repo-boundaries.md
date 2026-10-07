# ADR 0012: Repository boundaries for FloppyLM, xbox-gpu-training and xllama

## Status

`accepted` — accepted 2026-10-01, by the owner.
Amends [ADR 0009](0009-xbox-e0-backend.md): extends it with repository boundaries; does not change its numerical
or scientific rules.

## Context

The E0 semantics were implemented in four places: this Python oracle, the
xbox-gpu-training E0 DX12 backend, its legacy Win32 phases 0–5, and a ggml CPU trainer
on xllama draft PR #301 (`feat/floppylm-training`, with its own ADR 0004/0005 and an
incompatible checkpoint format). Docs in xbox-gpu-training claimed that "the FloppyLM
CPU path lives in xllama" and that the FLP2 envelope belongs to xllama, contradicting
ADR 0009. Native backends were never compared with each other, only with this oracle.

## Decision

- **floppylm (this repository)** is the single source of truth for FloppyLM: model and
  codec semantics, FLP2 (`pack.py`, `rans.py`), the `floppylm.*.v1` job, result and
  checkpoint contracts, data, configs and scientific gates.
- **xbox-gpu-training** is the only native FloppyLM training backend: the E0 DX12/UWP
  executor. It consumes the contracts defined here and never defines FloppyLM
  semantics. Its Win32 phases 0–5 are diagnostic only and certify nothing for FloppyLM.
- **xllama** contains no FloppyLM logic. PR #301 is closed without merge; the branch
  stays on the remote as history only. xllama keeps inference and its own training lanes.
- A second native FloppyLM backend requires a superseding ADR here, including a
  cross-backend parity gate and a shared checkpoint contract.
- No shared D3D12, CI or deploy library across these repositories: the GPU code in
  xllama (inference GEMV/bandwidth) and xbox-gpu-training (training) has no overlap.

## Follow-ups (after the running E0 campaign; frozen trainer sources stay untouched)

- Publish the `floppylm.*.v1` contracts as JSON Schema files with golden fixtures, and
  have xbox-gpu-training test against them at a pinned floppylm commit.
- Move Xbox operations (`xbox.py`, `xbox_portal.py`) out of the core package and stop
  reading credentials from xllama's `~/.config/xllama/xbox-env`.

## Consequences

One implementation per role; a bug in E0 semantics is fixed in the oracle or the single
backend, never in a copy. xbox-gpu-training docs must refer here, not to xllama.

## Later (2026-10-07)

Campaign `e0-20261004T103838Z-c58a86` stopped on 2026-10-07. The two follow-ups above
remain open. This note does not change the decision.
