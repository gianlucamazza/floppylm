# E0 readiness observation — 2026-10-03

Purpose: preparation only. No campaign, job publication, final-test reservation,
recovery, app restart or package installation occurred.

[Preflight](preflight.json) passed through a dedicated Odroid tunnel with the
existing TLS pin. It records the exact source hashes and observation commit,
acceptance/benchmark hashes, train/validation bytes and hashes, accepted package,
worker/PID, reservation metadata and the phase cost envelope. Test data was not
opened. This observation is not a lease: rerun immediately before an authorized launch.

[Integration](integration.json) records merged FloppyLM #13/#14 and backend #39.
Runtime, UWP and contract trees match the qualified 0.1.0.98 CI source; no newer
CI package was deployed. The preflight source commit precedes this evidence-only
commit. The final operational checkout is checked again after integration; source
file hashes must still agree with this record. The final operational JSON is retained
locally at `runs/e0-readiness-20261003/operational.json`; it also binds the final
preflight script hash after the malformed-response guard was added.

One legacy local manifest (`fdab67`, package 0.1.0.56) still says `running` but
predates PID recording. Its original source `272b26c` holds a lifetime flock.
The existing lock has no owner in `/proc/locks`; this is reported as
`unowned_legacy_lock`, without changing the historical manifest. A missing lock,
held/waiting lock or unavailable kernel observation blocks readiness.

The six possible scale/MLP paths have 55–56 original trials and an extrapolated
44–48 GPU training hours before S3. An all-repair scenario adds roughly another
training pass, potentially with changed token counts. Host evaluation, packing,
transfer, downtime and final evaluation are excluded; host evaluation remains
unmeasured. These estimates are not a completion-time promise.

See the [launch packet](../../operations/e0-launch-packet.md) for exact arguments,
protocol and explicit launch/recovery boundaries. E0 is prepared, not running.
