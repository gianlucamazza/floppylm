# Stay-alive DisplayRequest package acceptance — 0.1.0.86 — 2026-10-02

Purpose: **functional**. This record does not certify language-model quality or restart a scientific campaign.

## Artifact and deployment

CI [36985816615](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/36985816615)
built source `12251a7ae205a72477bf98bd74a73c15faf44009` ([PR 34](https://github.com/gianlucamazza/xbox-gpu-training/pull/34)
drop Extended Execution on [PR 33](https://github.com/gianlucamazza/xbox-gpu-training/pull/33) process-lifetime
`DisplayRequest`).
The installed package is `GianlucaMazza.XgpuE0_0.1.0.86_x64__g0p5dcfz4t9z4`.
[package-lineage.json](package-lineage.json) records unsigned and signed SHA-256, preserved CI payloads, the existing development signing certificate and the pinned Device Portal TLS certificate.
Shader `Assets/e0_tensor.cso` matches 0.1.0.56, 0.1.0.68 and 0.1.0.80.

[openappx.json](openappx.json) and [tls-pin.json](tls-pin.json) are the same environment proofs as the 0.1.0.56 record.

In-place upgrade replaced 0.1.0.84. That package granted `extended_execution=allowed`; Dev Home steal-focus then let the lifecycle job run from trunk 832 to completed 1844 with no `.cancel`. 0.1.0.86 does not request Extended Execution. Idle tombstones still happened until host `openappx deploy --start` relaunched the process; Device Portal POST `/api/taskmanager/app` returned HTTP 400 while the process was gone. Recorded gates ran after that relaunch.

## Hardware gates

- [kernel-parity.json](kernel-parity.json): 52 GPU operation cases passed.
- [acceptance.json](acceptance.json): 36 fixtures, AdamW and exact resume passed.
- [worker.json](worker.json): wrong identity rejected as `claim_job_id_mismatch`; oversized command rejected as `invalid E0 command dimensions/buffers` (native command validation from xbox-gpu-training PR 29); worker reused.
- [runner-recovery.json](runner-recovery.json): exact interrupted recovery and completed-job idempotence passed.
- [lifecycle.json](lifecycle.json): real Dev Home suspension at trunk step 744 (`suspend` marker); producer reported `lifecycle_exact` and completed trunk 1844.
- [throughput.json](throughput.json): 9639.533 token/s, peak app memory 121786368 bytes, synthetic corpus (same recipe as 0.1.0.56/0.1.0.68/0.1.0.80).
- [bit-identity.json](bit-identity.json): identical numerical payloads for 38/38 acceptance cases versus 0.1.0.56; six raw branch files, two numerical checkpoint states, three benchmark artifact hashes and the shader hash agree. Canonical JSON excludes only declared execution telemetry.
- [bit-identity-vs-068.json](bit-identity-vs-068.json): the same comparison versus 0.1.0.68, also 38/38.
- [bit-identity-vs-080.json](bit-identity-vs-080.json): the same comparison versus 0.1.0.80, also 38/38.

[idle-cold.png](idle-cold.png) and [dashboard.png](dashboard.png) are Device Portal screenshots after the gates (1920×1080). Rolling UI throughput is not the whole-run benchmark average.

No extra `--steps 700` bench is part of this record.

Campaign `e0-20261001T163456Z-fdab67` stays bound to 0.1.0.56 and was not resumed.
Campaign `e0-20261002T072408Z-40a67c` stays bound to 0.1.0.80 and was not continued onto 0.1.0.86.

## Reproduction

Raw inputs remain under `runs/xbox-{acceptance,benchmark,worker,recovery,lifecycle}-20261002-ci36985816615c`.
The reference 0.1.0.56 dirs use suffix `ci36885338811`; 0.1.0.68 uses `ci36925453940`; 0.1.0.80 uses `ci36944493415c`.
`scripts/verify_e0_bit_identity.py` in xbox-gpu-training produced the bit-identity files.
The host worker oversized check accepts both `dispatch dimension` and `invalid E0 command dimensions/buffers`.
