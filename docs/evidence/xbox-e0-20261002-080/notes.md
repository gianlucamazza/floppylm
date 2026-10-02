# Dashboard liveness package acceptance — 0.1.0.80 — 2026-10-02

Purpose: **functional**. This record does not certify language-model quality or restart a scientific campaign.

## Artifact and deployment

CI [36944493415](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/36944493415)
built source `f2d2a23395e24d9b9f0c7df931c4e51116c43edd` ([PR 32](https://github.com/gianlucamazza/xbox-gpu-training/pull/32) dashboard liveness on [PR 30](https://github.com/gianlucamazza/xbox-gpu-training/pull/30) bounded GPU waits).
The installed package is `GianlucaMazza.XgpuE0_0.1.0.80_x64__g0p5dcfz4t9z4`.
[package-lineage.json](package-lineage.json) records unsigned and signed SHA-256, preserved CI payloads, the existing development signing certificate and the pinned Device Portal TLS certificate.
Shader `Assets/e0_tensor.cso` matches 0.1.0.56 and 0.1.0.68. The GPU fence wait is bounded (600 s, 250 ms poll).

[openappx.json](openappx.json) and [tls-pin.json](tls-pin.json) are the same environment proofs as the 0.1.0.56 record.

In-place upgrade replaced 0.1.0.76 (installed, never started). Two earlier host attempts ended when `XgpuE0.exe` left the process list with `device.json` still `ready` and Dev Home in the foreground; the recorded gates ran after relaunch.

## Hardware gates

- [kernel-parity.json](kernel-parity.json): 52 GPU operation cases passed.
- [acceptance.json](acceptance.json): 36 fixtures, AdamW and exact resume passed.
- [worker.json](worker.json): wrong identity rejected as `claim_job_id_mismatch`; oversized dispatch rejected; worker reused.
- [runner-recovery.json](runner-recovery.json): exact interrupted recovery and completed-job idempotence passed.
- [lifecycle.json](lifecycle.json): real Dev Home suspension at trunk step 550 (`suspend` marker); producer reported `lifecycle_exact` and completed trunk 1844.
- [throughput.json](throughput.json): 10017.993 token/s, peak app memory 125595648 bytes, synthetic corpus (same recipe as 0.1.0.56/0.1.0.68).
- [bit-identity.json](bit-identity.json): identical numerical payloads for 38/38 acceptance cases versus 0.1.0.56; six raw branch files, two numerical checkpoint states, three benchmark artifact hashes and the shader hash agree. Canonical JSON excludes only declared execution telemetry.
- [bit-identity-vs-068.json](bit-identity-vs-068.json): the same comparison versus 0.1.0.68, also 38/38.

[idle-cold.png](idle-cold.png) is the empty-state dashboard after start (`WORKER READY · heartbeat 2 s ago`, caption “No job yet · waiting for a job from the host”).
[dashboard.png](dashboard.png) shows the accepted package/source after the gates (`WORKER READY · heartbeat 1 s ago · fence 7 602`). Rolling UI throughput is not the whole-run benchmark average.

No extra `--steps 700` bench is part of this record.

Campaign `e0-20261001T163456Z-fdab67` stays bound to 0.1.0.56 and was not resumed.

## Reproduction

Raw inputs remain under `runs/xbox-{acceptance,benchmark}-20261002-ci36944493415c` and
`runs/xbox-{worker,recovery,lifecycle}-20261002-ci36944493415d`.
The reference 0.1.0.56 dirs use suffix `ci36885338811`; 0.1.0.68 uses `ci36925453940`.
`scripts/verify_e0_bit_identity.py` in xbox-gpu-training produced the bit-identity files.
The host worker identity check accepts both `job_id must match` and persist_claim `claim_job_id_mismatch`.
