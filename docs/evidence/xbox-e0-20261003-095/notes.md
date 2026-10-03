# Published-fence watchdog package acceptance — 0.1.0.95 — 2026-10-03

Purpose: **functional**. This record does not certify language-model quality or restart a scientific campaign.

## Artifact and deployment

CI [37077527029](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/37077527029)
built source `7cb3fcfcc8490477b0ac900356af53cd487d4d7c` ([PR 38](https://github.com/gianlucamazza/xbox-gpu-training/pull/38)
published-fence watchdog on [PR 37](https://github.com/gianlucamazza/xbox-gpu-training/pull/37) fence poll wait).
The installed package is `GianlucaMazza.XgpuE0_0.1.0.95_x64__g0p5dcfz4t9z4`.
[package-lineage.json](package-lineage.json) records unsigned and signed SHA-256, preserved CI payloads, the existing development signing certificate and the pinned Device Portal TLS certificate.
Shader `Assets/e0_tensor.cso` matches 0.1.0.56, 0.1.0.68, 0.1.0.80, 0.1.0.86 and 0.1.0.93.
The Win32 GPU wait still polls `GetCompletedValue` and `Sleep`. A second watch samples the published fence from the heartbeat thread and, after 600 seconds frozen, records `gpu_wait_timeout`, interrupts a running checkpoint when one exists, and exits the process. These gates did not observe that timeout.

The install checked the live Device Portal pin against the existing `xbox.env` pin and used openappx 0.7.0. The wrong-pin refusal test from the 0.1.0.56 record was not repeated.

In-place upgrade replaced 0.1.0.93. Campaign `e0-20261002T191632Z-ca781f` stays bound to 0.1.0.93 and was not recovered onto 0.1.0.95.

## Hardware gates

- [kernel-parity.json](kernel-parity.json): 52 GPU operation cases passed.
- [acceptance.json](acceptance.json): 36 fixtures, AdamW and exact resume passed.
- [worker.json](worker.json): wrong identity rejected as `claim_job_id_mismatch`; oversized command rejected as `invalid E0 command dimensions/buffers`; worker reused.
- [runner-recovery.json](runner-recovery.json): exact interrupted recovery and completed-job idempotence passed.
- [lifecycle.json](lifecycle.json): real Dev Home suspension (`suspend` marker); producer reported `lifecycle_exact` and completed trunk 1844.
- [throughput.json](throughput.json): 9752.238 token/s, peak app memory 123494400 bytes, synthetic corpus (same recipe as 0.1.0.56/0.1.0.68/0.1.0.80/0.1.0.86/0.1.0.93).
- [bit-identity.json](bit-identity.json): identical numerical payloads for 38/38 acceptance cases versus 0.1.0.56; six raw branch files, two numerical checkpoint states, three benchmark artifact hashes and the shader hash agree. Canonical JSON excludes only declared execution telemetry (`loss_series` included in that ignore set).
- [bit-identity-vs-068.json](bit-identity-vs-068.json), [bit-identity-vs-080.json](bit-identity-vs-080.json), [bit-identity-vs-086.json](bit-identity-vs-086.json), [bit-identity-vs-093.json](bit-identity-vs-093.json): the same comparison versus 0.1.0.68, 0.1.0.80, 0.1.0.86 and 0.1.0.93, each 38/38.

[dashboard.png](dashboard.png) is the Device Portal screenshot after the gates (worker `ready`, no active job, last job the lifecycle run at trunk 1844, package `0.1.0.95`, commit `7cb3fcf`). Rolling UI throughput is not the whole-run benchmark average. There is no separate cold-idle capture.

No extra `--steps 700` bench is part of this record.

Campaign `e0-20261001T163456Z-fdab67` stays bound to 0.1.0.56.
Campaign `e0-20261002T072408Z-40a67c` stays bound to 0.1.0.80.
Campaign `e0-20261002T090742Z-2fe64f` stays bound to 0.1.0.86.
Campaign `e0-20261002T191632Z-ca781f` stays bound to 0.1.0.93.

## Reproduction

Raw inputs remain under `runs/xbox-{acceptance,benchmark,worker,recovery,lifecycle}-20261003-ci37077527029`.
The reference 0.1.0.56 dirs use suffix `ci36885338811`; 0.1.0.68 uses `ci36925453940`; 0.1.0.80 uses `ci36944493415c`; 0.1.0.86 uses `ci36985816615c`; 0.1.0.93 uses `ci37049627510`.
`scripts/verify_e0_bit_identity.py` in xbox-gpu-training produced the bit-identity files.
