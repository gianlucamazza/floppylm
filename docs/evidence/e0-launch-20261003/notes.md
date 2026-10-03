# E0 authorized launch on package 0.1.0.98

The owner explicitly confirmed a new E0 campaign, including the reserved final test
only after the accepted scientific gates. This record proves launch and initial
progress; it is not a completed campaign or a scientific quality result.

## Frozen identity

- Campaign: `e0-20261003T104407Z-a8d8b9`, created `2026-10-03T10:44:07Z`.
- Directory: `runs/e0-campaign-20261003-098`.
- Host source: `8867ec6c773bfd8d1b2c87ba02fea8757d1befcb`, clean at launch.
- Package: `GianlucaMazza.XgpuE0_0.1.0.98_x64__g0p5dcfz4t9z4`.
- Backend source: `cc134fe4458ffa51c73331ee6dd6af4a6ae8b0d7`, qualified CI
  [37112204165](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/37112204165).
- [Preflight](preflight.json): positive at `2026-10-03T10:43:09Z`, full train/val
  hashes, idle live worker, no pending jobs, existing TLS pin unchanged.
- [Launch command](launch.json): exact acceptance and throughput paths, environment
  and supervision properties. Historical campaigns remain retired.

ADR 0015 and the integrated ADR 0018 correctness checks remain unchanged. The
campaign executes the neutral selections, tuning, grids and paired seeds, stops
on a failed comparison gate, and freezes ten verified artifacts before reserving
the single final evaluation. No final evaluation has occurred at this observation.

## Operational supervision

Three transient user services use suffix `20261003T104300Z`: `floppylm-e0-tunnel`,
`floppylm-e0-campaign` and `floppylm-e0-monitor`. Linger is enabled. The dedicated
SSH tunnel goes through Odroid to the console's Device Portal; it does not depend
on the invoking terminal. All services have `Restart=no`. The campaign uses
`KillMode=mixed` and an unlimited stop timeout to allow its existing cooperative
child cleanup. The read-only monitor observes every 30 seconds and is bound to
the campaign service. It never cancels, restarts or requeues work.

The current owner instruction requires `bg` for CPU-heavy work. Both campaign and
monitor run through that wrapper with an explicit `background.slice`, superseding
the historical `app.slice` exception for this launch. The slice has CPU weight 30
and an observed one-CPU quota. No machine configuration or accepted ADR was edited.
The 44–48 GPU-hour projection excludes host evaluation, repairs and downtime.

The exact unit snapshots, logs and authorization record are retained under
`runs/e0-launch-20261003T104300Z/`; all three unit snapshots passed
`systemd-analyze --user verify` ([result](unit-verification.txt)). Durable temporal
observations are in the campaign's `monitor.jsonl`, with latest `monitor.json`.

## Independent initial progress proof

[Two direct worker observations](gpu-progress.json), at 10:46:02Z and 10:47:35Z,
bind the same job/hash, worker and exact package. Trunk steps advance from 75 to
197, completed fences from 11597 to 15505, and the heartbeat advances. The
[status snapshot](status.json) independently contains a published checkpoint and
matching source/device provenance on hardware adapter `SraKmd_arden`.

The host status CLI reports `lock_unverified` on this Btrfs filesystem: `stat`
reports device `0:51`, while kernel lock records use `00:24` for the same inode.
The existing implementation requires equal devices and cannot match them.
[Direct process descriptor evidence](host-locks.json) verifies the campaign and
trial PIDs each hold the expected exclusive FLOCK on the exact resolved lock path.
The failure is in lock observation, not a missing lock. Frozen runtime sources
remain unchanged; after the campaign releases its source freeze, correct the
canonical `runlog.host_liveness` implementation using descriptor identity and add
a Btrfs regression test. Review the legacy preflight lock path under the same
policy. Do not interpret `lock_unverified` alone as proof of host death or recovery
authorization.
