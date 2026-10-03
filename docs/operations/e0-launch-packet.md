# E0 launch packet: preparation only

This packet does not launch or reserve a campaign. The current accepted hardware
is [package 0.1.0.98](../evidence/xbox-e0-20261003-098/notes.md). The source of live
project state remains [STATUS](../STATUS.md). All historical campaigns stay retired.

## Provenance and preflight

FloppyLM PRs #13 and #14 and backend PR #39 are integrated. The merged backend's
runtime, UWP and contract files equal the qualified CI source `cc134fe4`; merge CI
artifacts with newer package numbers are not substitutes for the installed package.
The next campaign freezes the integrated host sources including the readiness
change; it never reuses a historical campaign manifest or run identity.

From the operational checkout, open a dedicated tunnel in a separate terminal:

```bash
ssh -S none -N -o BatchMode=yes -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=15 \
  -L 127.0.0.1:31443:192.168.1.44:11443 odroid
```

Use the existing pinned certificate and credentials from `xbox.env`. Do not change
that file or re-pin. Run this read-only check, retaining stdout in a new evidence file:

```bash
XBOX_IP=127.0.0.1 XBOX_PORT=31443 \
XGPU_E0_PACKAGE=GianlucaMazza.XgpuE0_0.1.0.98_x64__g0p5dcfz4t9z4 \
.venv/bin/python scripts/e0_preflight.py --xbox \
  --acceptance docs/evidence/xbox-e0-20261003-098/acceptance.json \
  --benchmark docs/evidence/xbox-e0-20261003-098/throughput.json \
  --data-manifest runs/e0-20261002T191632Z-ca781f-000/manifest.json
```

The historical manifest supplies corpus hashes only; it does not authorize recovery.
The preflight verifies the full train/validation byte streams. It records existing
repair/final-test reservation metadata and campaign-host liveness, without reading
the test split or changing any records. Missing references, dirty source, wrong
package, busy worker, stale heartbeat or pending inbox work fail readiness. An old
`running` manifest whose original process is dead is reported as historical metadata;
it is not rewritten or treated as live work. Unverified host liveness fails closed.

The JSON includes the observed host commit and frozen-source hashes, hardware
package/source, acceptance/benchmark hashes, corpus reference hash, protocol,
reservation metadata and cost projection. A local-only pass is not console readiness.

## Frozen execution protocol

Keep ADR 0015 and S1–S10 unchanged: 1/16 budget; byte tokenizer; neutral scale/MLP
selection with seeds 0/1; six tuning trials per arm; solver grids; five paired seeds
per arm. Enumerations come from `floppylm.campaign_protocol`, also consumed by the
launcher. T is 20 times stored parameters, with T/2T/4T branches. Only one S3 repair
per trial is allowed. No fill-aware solver or E1 change enters this freeze.

Require serialized individual/reciprocal byte parity and rank stability at T/2T/4T.
Saturation is recorded, not an eligibility gate. A failed comparison stops the
campaign. Freeze ten verified artifacts before the single reserved final evaluation.
No final-test reservation is created during this preparation.

## Cost envelope

The preflight enumerates all six possible scale/MLP selections and derives schedules
from actual solver shapes, without choosing winners. With the accepted synthetic
rate, the estimate is 55–56 original trials and approximately 44–48 GPU training
hours before repairs. These are extrapolations across shapes, not measured campaign
durations or time limits. Full S3 incidence may require roughly another training
pass, with different token counts after resizing.

Host validation, packing, upload, final evaluation and downtime are separate and
not included. Host evaluation duration is explicitly unknown; this packet makes no
end-to-end completion promise. Route CPU-heavy work according to the owner's current
host policy; historical throughput does not prove performance under different caps.

## Explicit launch and observation

Launch remains a separate owner action after a fresh positive preflight and source
freeze. The entrypoint below is prepared, **not executed**; supply a fresh unique
output directory and use the supervised launcher described in the [runbook](xbox-e0.md):

```bash
.venv/bin/python -u experiments/e0_campaign.py \
  --out runs/e0-campaign-<new-unique-id> \
  --acceptance docs/evidence/xbox-e0-20261003-098/acceptance.json \
  --benchmark docs/evidence/xbox-e0-20261003-098/throughput.json
```

Carry the tunnel environment into the supervised process and keep the tunnel alive
for the campaign. Keep the Xbox app foreground and package unchanged. Use
`scripts/e0_status.py --campaign <new-directory> --xbox` to observe owner/hash,
heartbeat, completed work and checkpoints. Transport failure is unknown progress,
not a reason to cancel/restart. After a fault, diagnose evidence first and recover
explicitly on the same package. Never run a keep-alive/requeue loop.
