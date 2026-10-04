# Published-fence classification qualification — 0.1.0.102

Purpose: **functional**. No scientific campaign was resumed onto this package.
Historical campaigns keep their original package and source bindings.

## Package and scope

The installed Release package is `GianlucaMazza.XgpuE0_0.1.0.102_x64__g0p5dcfz4t9z4`, built by
CI [37186655285](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/37186655285)
from squash `4b8f51c3a5ee985ce8fcb71327f0ffc88e487545`
([PR #40](https://github.com/gianlucamazza/xbox-gpu-training/pull/40), PR head `bd9dfb4`).
[Lineage](package-lineage.json) binds the unsigned and signed package hashes and the
preserved CI payloads. Signing used the existing development certificate. Deployment
used the existing Odroid SSH tunnel and the TLS pin already published for 0.1.0.98.
That pin matched; it was not replaced. No uninstall was required: the install replaced
0.1.0.98 in place and kept LocalState.

The post-install start command returned HTTP 400. The process list, `device.json`,
and an advancing heartbeat then showed this package, source prefix `4b8f51c3a5ee`,
ready, with no active job.

The host recovery harness on the first pass still treated a recorded native interrupt
as a missing exception. FloppyLM [PR #19](https://github.com/gianlucamazza/floppylm/pull/19)
(`555a865`) accepts runner exit 130 with summary status `interrupted`. Recovery,
lifecycle, benchmark and bit identity below are the rerun after that fix. Acceptance,
the watchdog probe and the worker gate are from the first pass on this same package.
The first recovery directory remains `runs/xbox-recovery-20261004-ci37186655285/` and
is not this proof.

## Measured hardware gates

- [Acceptance](acceptance.json): 36 fixtures, 52 independent GPU operation cases
  ([kernel proof](kernel-parity.json)), AdamW and exact resume passed.
- [Watchdog](watchdog.json): the parked probe published checkpoint step 2, the
  ordinary heartbeat advanced, and the process exited after 602.687 seconds.
  The [fault](watchdog-fault.json) is `progress_stall`, requested fence 0, elapsed
  600819 ms, error “published progress frozen without an in-flight GPU request”.
  [Process exit](process-exit.json) and [runtime events](runtime-events.jsonl)
  record that observation. Exact recovery of the control matched.
- One explicit restart produced a [new idle worker](worker-after-restart.json).
- [Worker guards](worker.json) passed.
- [Recovery](recovery.json): the interrupted runner returned 130 with summary
  `interrupted`, resume completed, and a second resume left the summary unchanged.
  Branch and checkpoint recovery of the interrupted job matched the full job.
- [Real Dev Home suspension](lifecycle.json) interrupted at trunk step 83 on
  adapter `SraKmd_arden` and recovered exactly.
- [Bit identity](bit-identity.json) versus accepted 0.1.0.98: 38/38 canonical
  acceptance payloads, six raw branch files, two numerical checkpoint states,
  three benchmark branch hashes and the shader CSO agree. Shader SHA-256 is
  `a6e6c2f641b6a1362e69c06d92f4faf2ae86b41baea9a681a86655ac994ca50f`.
  Only declared execution telemetry is excluded. Reference
  [lineage](reference-098/package-lineage.json) and
  [benchmark](reference-098/throughput.json) are byte-preserved copies of the
  0.1.0.98 record.
- [Synthetic benchmark](throughput.json): 9757.404 token/s; peak app memory
  128167936 bytes. This is functional throughput, not a quality result and not
  a controlled performance claim.
- [Preservation](preservation.json): the pre-existing inbox inventory hash was
  unchanged. Archived payload bytes were not rehashed. The worker observed after
  these gates was idle.

No dashboard image was captured for this package.

The initiating cause of the historical scientific stall remains unproven. This
package corrects the published-fence classification (`progress_stall` when no GPU
wait is in flight) and the host records an interrupted native result as
interrupted. It does not establish why checkpoint publication stopped at step 3008,
and it does not authorize migrating `a8d8b9` or any earlier campaign.

## Reproduction and raw evidence

Raw run directories, relative to the repository:

- `runs/xbox-acceptance-20261004-ci37186655285/`
- `runs/xbox-watchdog-20261004-ci37186655285/`
- `runs/xbox-worker-20261004-ci37186655285/`
- `runs/xbox-recovery-20261004-ci37186655285-r2/`
- `runs/xbox-lifecycle-20261004-ci37186655285/`
- `runs/xbox-benchmark-20261004-ci37186655285/`
- `runs/xbox-bit-identity-20261004-ci37186655285.json`

Run acceptance, then the watchdog harness with that acceptance, then worker,
recovery, lifecycle and benchmark. `scripts/verify_e0_bit_identity.py` compares
the candidate with `runs/watchdog-release-20261003-ci37112204165/`.
