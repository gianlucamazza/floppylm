"""Worker ownership and temporal liveness; observations never cancel GPU work."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

HEARTBEAT_TIMEOUT = 30.0
PROGRESS_TIMEOUT = 600.0


def validate_worker(value: dict, package: str, commit: str | None = None) -> dict:
    """Validate the runtime contract before using it as recovery authority."""
    if not isinstance(value, dict) or value.get("schema") != "floppylm.worker.v1":
        raise RuntimeError(
            "worker contract missing or unsupported; new runtime acceptance required"
        )
    if value.get("package") != package or (commit and value.get("commit") != commit):
        raise RuntimeError("worker package/source differs from bound device")
    if not all(isinstance(value.get(k), str) and value[k] for k in ("worker_id", "commit")):
        raise RuntimeError("worker identity is incomplete")
    for key in ("pid", "heartbeat_seq"):
        if type(value.get(key)) is not int or value[key] < (1 if key == "pid" else 0):
            raise RuntimeError("invalid worker " + key)
    if value.get("state") not in ("starting", "ready", "running", "failed"):
        raise RuntimeError("invalid worker state")
    active = value.get("active_job")
    if active is not None and (
        not isinstance(active, dict)
        or not isinstance(active.get("job_id"), str)
        or not active["job_id"]
        or not re.fullmatch(r"[a-f0-9]{64}", str(active.get("job_sha256", "")))
    ):
        raise RuntimeError("invalid active worker binding")
    if "active_job" not in value or "fault" not in value:
        raise RuntimeError("worker activity/fault field missing")
    progress = value.get("progress")
    if (
        not isinstance(progress, dict)
        or any(
            type(progress.get(k)) is not int or progress[k] < 0
            for k in ("sequence", "trunk_step", "cooldown_step", "completed_fence")
        )
        or any(not isinstance(progress.get(k), str) for k in ("phase", "operation"))
    ):
        raise RuntimeError("invalid worker progress")
    fault = value["fault"]
    if fault is not None and (
        not isinstance(fault, dict)
        or any(not isinstance(fault.get(k), str) or not fault[k] for k in ("kind", "error"))
        or any(
            type(fault.get(k)) is not int or fault[k] < 0
            for k in ("requested_fence", "completed_fence", "elapsed_ms")
        )
    ):
        raise RuntimeError("invalid worker fault")
    return value


def owns(worker: dict, job_id: str, job_sha: str) -> bool:
    return worker["state"] == "running" and worker["active_job"] == {
        "job_id": job_id,
        "job_sha256": job_sha,
    }


def progress_marker(report: dict, worker: dict | None = None) -> tuple:
    """Count completed work, including cooldown progress, not heartbeats/log lines."""
    marker = (
        report.get("trunk_step"),
        report.get("phase"),
        report.get("cooldown_step"),
        tuple(b.get("end_step") for b in report.get("branches", [])),
    )
    if worker is not None:
        p = worker["progress"]
        marker += (p["sequence"], p["completed_fence"])
    return marker


@dataclass
class RuntimeMonitor:
    job_id: str
    job_sha: str
    worker_id: str | None = None
    heartbeat_seq: int | None = None
    heartbeat_at: float | None = None
    progressed_at: float | None = None
    marker: tuple | None = None
    observed_live: bool = False
    observed_progress: bool = False
    alarms: set = field(default_factory=set)

    def observe(self, report: dict, worker: dict, now: float) -> dict:
        issues = []
        if report.get("job_sha256") != self.job_sha:
            issues.append("job_binding_mismatch")
        if self.worker_id is not None and self.worker_id != worker["worker_id"]:
            issues.append("worker_instance_changed")
            self.observed_live = self.observed_progress = False
            self.heartbeat_seq = self.heartbeat_at = None
            self.marker = self.progressed_at = None
        if self.worker_id is None:
            self.worker_id = worker["worker_id"]
        if self.heartbeat_seq is not None and worker["heartbeat_seq"] < self.heartbeat_seq:
            issues.append("heartbeat_sequence_regressed")
            self.observed_live = False
        if self.heartbeat_seq is None or worker["heartbeat_seq"] > self.heartbeat_seq:
            self.observed_live |= self.heartbeat_seq is not None
            self.heartbeat_seq = worker["heartbeat_seq"]
            self.heartbeat_at = now
        if report.get("state") == "running" and not owns(worker, self.job_id, self.job_sha):
            issues.append("running_job_has_no_matching_owner")
        if worker["state"] == "failed" or worker["fault"] is not None:
            issues.append("worker_fault")
        heartbeat_age = now - self.heartbeat_at if self.heartbeat_at is not None else 0.0
        if heartbeat_age >= HEARTBEAT_TIMEOUT:
            issues.append("worker_heartbeat_stalled")
        marker = progress_marker(report, worker)
        if self.marker is not None and (
            worker["progress"]["sequence"] < self.marker[-2]
            or worker["progress"]["completed_fence"] < self.marker[-1]
        ):
            issues.append("progress_sequence_regressed")
        elif marker != self.marker:
            self.observed_progress |= self.marker is not None
            self.marker, self.progressed_at = marker, now
        progress_age = now - self.progressed_at if self.progressed_at is not None else 0.0
        if report.get("state") == "running" and progress_age >= PROGRESS_TIMEOUT:
            issues.append("no_progress")
        current = set(issues)
        events = sorted(current - self.alarms)
        cleared = sorted(self.alarms - current)
        self.alarms = current
        return {
            "worker_id": self.worker_id,
            "issues": issues,
            "events": events,
            "cleared": cleared,
            "heartbeat_age_seconds": heartbeat_age,
            "progress_age_seconds": progress_age,
            "liveness": "unavailable"
            if set(issues) - {"no_progress"}
            else "live"
            if self.observed_live
            else "unverified",
            "progress": "stalled"
            if "no_progress" in issues
            else "observed"
            if self.observed_progress
            else "unverified",
        }
