# ADR 0006: FLP2 is the only supported format

## Status

`accepted` — accepted 2026-09-30.
Supersedes in part [ADR 0005](0005-e0v2-protocol.md) §10: the "including the legacy `FLP1`" part.
The rest of ADR 0005 remains valid.

## Context

ADR 0005 §10 also required reading and re-saving the `FLP1` artifacts of the pre-v2 E0-lite
grid. The user then asked to avoid unnecessary legacy code and architecture. No
E0 v2 path depends on `FLP1`: the pre-v2 artifacts are diagnostics excluded from verdicts
([pre-v2](../evidence/e0-lite/pre-v2/notes.md)), and their format required a 12-bit rANS
decoder, its own scale rules and an architecture variant.

## Decision

1. Active code supports only `FLP2`, with byte-identical round-trip (`pack(unpack(b)) == b`).
2. An `FLP1` blob is rejected with an explicit `FormatError` that names the reference revision.
3. Git revision **`f9e0732`** is the reference for reading the historical artifacts. There it is
   verified that the three `FLP1` blobs re-save identically and that `experiments/verify_pre_v2.py`
   exactly reproduces the recorded val bpb (d64L6 2.0129680935772494, d80L4
   1.8551768137161695).
4. The pre-v2 artifacts remain on disk (outside Git) and are documented with their hashes.

## Consequences

- Removed from active code: the 12-bit rANS decoder, the `flp1` quantization rule, the
  `rule` configuration field, the `FLP1` branch of `pack`/`unpack`, the verification script and the
  old `e0_lite.py` harness.
- `tests/fixtures/flp1_smoke.flp` stays in the repo only for the rejection test.
