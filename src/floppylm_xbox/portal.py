"""Device Portal transport for the separately packaged E0 Xbox app.

Credentials remain outside jobs/evidence. Content-addressed chunks make interrupted
uploads resumable; the native receiver verifies each chunk and the assembled asset.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import json
import os
import shlex
import ssl
import time
import uuid
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from floppylm import runlog

CHUNK_BYTES = 2 << 20
CREDENTIAL_KEYS = ("XBOX_IP", "XBOX_USER", "XBOX_PASS", "XBOX_CERT_SHA256")
DEFAULT_PORT = 11443
DEFAULT_PACKAGE_NAME = "XgpuE0"


def env_file() -> Path:
    """Connection settings file: $FLOPPYLM_XBOX_ENV or ~/.config/floppylm/xbox.env."""
    configured = os.environ.get("FLOPPYLM_XBOX_ENV")
    return Path(configured) if configured else Path.home() / ".config/floppylm/xbox.env"


def read_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines (optional `export`, comments, shell quoting) without a shell."""
    if not path.is_file():
        return {}
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, raw = line.removeprefix("export ").strip().partition("=")
        if sep and key.isidentifier():
            parts = shlex.split(raw, comments=True)
            values[key] = parts[0] if parts else ""
    return values


ACCEPTANCE_SCHEMA = "floppylm.xbox.acceptance.v1"


def check_acceptance(proof: dict, device: dict, package: str) -> None:
    """Scientific runs bind a passing acceptance measured on this exact package and commit."""
    if proof.get("schema") != ACCEPTANCE_SCHEMA or not proof.get("ok"):
        raise RuntimeError("invalid Xbox acceptance evidence")
    if not proof.get("kernels", {}).get("ok"):
        raise RuntimeError("scientific Xbox runs require per-operation acceptance evidence")
    if not device.get("commit") or proof.get("commit") != device.get("commit"):
        raise RuntimeError("acceptance source commit differs from running package")
    if proof.get("package") != package:
        raise RuntimeError("acceptance was measured on a different package")


def check_capabilities(config: dict, device: dict) -> None:
    """Refuse a config the device reports it cannot train (floppylm.device.v1 capabilities)."""
    caps = device.get("capabilities")
    if caps is None:
        return  # packages built before the capability report
    unsupported = [
        f"{key}={config[key]!r}"
        for key in ("vocab", "emb_fmt", "core_fmt", "mlp", "scale_policy")
        if config[key] not in caps[key]
    ]
    delta = caps["delta"]
    if not delta["minimum"] <= config["delta"] < delta["exclusive_maximum"]:
        unsupported.append(f"delta={config['delta']!r}")
    if unsupported:
        raise RuntimeError("backend does not support " + ", ".join(unsupported))


def certificate_fingerprint(value: str) -> str:
    """Normalize a SHA-256 certificate fingerprint (hex, colons and case ignored)."""
    digest = value.replace(":", "").strip().lower()
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("XBOX_CERT_SHA256 must be the SHA-256 of the DER certificate")
    return digest


def package_matches(full_name: str, name: str) -> bool:
    """True when the package identity name is `name`, with or without a publisher prefix."""
    identity = full_name.split("_", 1)[0]
    return identity == name or identity.endswith("." + name)


class Portal:
    def __init__(self, url: str, user: str, password: str, package: str, *, cert_sha256: str):
        target = urlsplit(url)
        if target.scheme != "https" or target.path not in ("", "/"):
            raise ValueError("Device Portal must be an HTTPS origin")
        self.host, self.port = target.hostname, target.port or DEFAULT_PORT
        self.package = package
        # Device Portal serves a self-signed certificate: trust is the pinned
        # fingerprint, checked on every connection, not a CA chain or hostname.
        self.cert_sha256 = certificate_fingerprint(cert_sha256)
        self.context = ssl.create_default_context()
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE
        self._cookies = SimpleCookie()
        self._csrf = ""
        self._authorization = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()

    @classmethod
    def configured(cls, package: str = "") -> Portal:
        # Environment first, then the env file; never print the result.
        settings = {**read_env_file(env_file()), **os.environ}
        missing = [k for k in CREDENTIAL_KEYS if not settings.get(k)]
        if missing:
            raise RuntimeError(
                f"Device Portal settings missing: {', '.join(missing)} "
                f"(set them in the environment or in {env_file()})"
            )
        portal = cls(
            f"https://{settings['XBOX_IP']}:{settings.get('XBOX_PORT') or DEFAULT_PORT}",
            settings["XBOX_USER"],
            settings["XBOX_PASS"],
            package,
            cert_sha256=settings["XBOX_CERT_SHA256"],
        )
        if not package:
            portal.package = settings.get("XGPU_E0_PACKAGE", "")
        if not portal.package:
            name = settings.get("XGPU_E0_PACKAGE_NAME") or DEFAULT_PACKAGE_NAME
            installed = portal.request("GET", "/api/app/packagemanager/packages", json_result=True)
            matches = [
                p["PackageFullName"]
                for p in installed["InstalledPackages"]
                if package_matches(p.get("PackageFullName", ""), name)
            ]
            if len(matches) != 1:
                raise RuntimeError(f"expected exactly one installed {name} package")
            portal.package = matches[0]
        return portal

    def request(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        headers: dict | None = None,
        *,
        json_result: bool = False,
    ):
        if method in ("POST", "DELETE") and not self._csrf:
            self.request("GET", "/")
            if not self._csrf:
                raise RuntimeError("Device Portal did not issue a CSRF cookie")
        connection = http.client.HTTPSConnection(
            self.host, self.port, context=self.context, timeout=120
        )
        try:
            connection.connect()
            certificate = connection.sock.getpeercert(binary_form=True) or b""
            if hashlib.sha256(certificate).hexdigest() != self.cert_sha256:
                raise ssl.SSLCertVerificationError(
                    "Device Portal certificate does not match XBOX_CERT_SHA256"
                )
            connection.request(
                method,
                path,
                body=body,
                headers={
                    "Authorization": self._authorization,
                    "Cookie": "; ".join(
                        f"{key}={value.value}" for key, value in self._cookies.items()
                    ),
                    **({"X-CSRF-Token": self._csrf} if self._csrf else {}),
                    **(headers or {}),
                },
            )
            response = connection.getresponse()
            for key, value in response.getheaders():
                if key.lower() == "set-cookie":
                    self._cookies.load(value)
            if "CSRF-Token" in self._cookies:
                self._csrf = self._cookies["CSRF-Token"].value
            payload = response.read()
            if response.status == 404:
                raise FileNotFoundError(path)
            if not 200 <= response.status < 300:
                detail = {}
                try:
                    error_body = json.loads(payload)
                    if isinstance(error_body, dict):
                        detail = {
                            k: error_body[k]
                            for k in ("ErrorCode", "ErrorMessage", "HResult")
                            if k in error_body
                        }
                except (ValueError, UnicodeDecodeError):
                    pass
                raise RuntimeError(
                    f"Device Portal {method} failed: HTTP {response.status} "
                    + json.dumps(detail)[:1000]
                )
            return json.loads(payload) if json_result else payload
        finally:
            connection.close()

    def path(self, endpoint: str, directory: str, filename: str | None = None) -> str:
        query = {
            "knownfolderid": "LocalAppData",
            "packagefullname": self.package,
            "path": "\\LocalState\\" + directory.replace("/", "\\"),
        }
        if filename is not None:
            query["filename"] = filename
        return "/api/filesystem/apps/" + endpoint + "?" + urlencode(query)

    def files(self, directory: str = "inbox") -> dict[str, int]:
        listing = self.request("GET", self.path("files", directory), json_result=True)
        return {
            item["Name"]: int(item["FileSize"]) for item in listing["Items"] if item["Type"] == 32
        }

    def get(self, filename: str, directory: str = "inbox") -> bytes:
        return self.request("GET", self.path("file", directory, filename))

    def upload(self, filename: str, data: bytes, directory: str = "inbox") -> None:
        if not filename or any(c in filename for c in '\\/"\r\n'):
            raise ValueError("unsafe remote filename")
        boundary = uuid.uuid4().hex
        header = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            f'filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'
        ).encode()
        payload = header + data + f"\r\n--{boundary}--\r\n".encode()
        self.request(
            "POST",
            self.path("file", directory, filename),
            payload,
            {"Content-Type": "multipart/form-data; boundary=" + boundary},
        )

    def asset(self, path: Path, existing: dict[str, int]) -> dict:
        digest = runlog.sha256_file(path)
        name = digest + ".bin"
        size = path.stat().st_size
        result = {"path": name, "bytes": size, "sha256": digest}
        if existing.get(name) == size:
            return result
        chunks = []
        with path.open("rb") as file:
            while block := file.read(CHUNK_BYTES):
                chunk_hash = hashlib.sha256(block).hexdigest()
                chunk_name = chunk_hash + ".chunk"
                if existing.get(chunk_name) != len(block):
                    self.upload(chunk_name, block)
                    existing[chunk_name] = len(block)
                chunks.append({"path": chunk_name, "bytes": len(block), "sha256": chunk_hash})
        result["chunks"] = chunks
        return result

    def submit(self, root: Path, *, purpose: str, acceptance: Path | None = None) -> dict:
        if (root / "publication.json").exists() or (root / "submitted.json").exists():
            raise RuntimeError("existing publication requires explicit recovery")
        device = json.loads(self.get("device.json", directory=""))
        if device.get("state") != "ready" or not device.get("hardware_gpu"):
            raise RuntimeError("E0 app is not ready on a hardware GPU")
        if device["package"] != self.package:
            raise RuntimeError("device package differs from requested package")
        if purpose == "scientific":
            if acceptance is None:
                raise RuntimeError("scientific Xbox runs require acceptance evidence")
            check_acceptance(json.loads(acceptance.read_text()), device, self.package)
        job = json.loads((root / "job.json").read_text())
        try:
            self.status(job["job_id"])
        except FileNotFoundError:
            pass
        else:
            raise RuntimeError("remote execution already exists; explicit recovery required")
        check_capabilities(job["config"], device)
        if purpose == "scientific":
            from .jobs import zero_row_gate

            if job["config"]["scale_policy"] not in ("row16", "row8log"):
                raise RuntimeError("ADR 0011 excludes tensor16 from scientific E0")
            gate = zero_row_gate(job["config"]["scale_policy"], job["config"]["core_fmt"])
            runlog.write_json(root / "zero-row-gate.json", gate)
            if not gate["ok"]:
                raise RuntimeError("scientific scale policy violates accepted S9 zero-row gate")
        existing = self.files()
        for key in ("initialization", "data", "indices"):
            path = root / job[key]["path"]
            digest = runlog.sha256_file(path)
            job[key] = {"path": digest + ".bin", "bytes": path.stat().st_size, "sha256": digest}
            if existing.get(job[key]["path"]) != job[key]["bytes"]:
                chunks = []
                with path.open("rb") as file:
                    while block := file.read(CHUNK_BYTES):
                        sha = hashlib.sha256(block).hexdigest()
                        chunks.append({"path": sha + ".chunk", "bytes": len(block), "sha256": sha})
                job[key]["chunks"] = chunks
        job["purpose"] = purpose
        if acceptance:
            job["acceptance_sha256"] = runlog.sha256_file(acceptance)
        self._publish(root, job, "submit")
        return job

    @staticmethod
    def _durable_json(path: Path, value: dict) -> None:
        runlog.write_json(path, value)
        with path.open("rb") as file:
            os.fsync(file.fileno())
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _publish(self, root: Path, job: dict, kind: str) -> None:
        journal_path = root / "publication.json"
        if journal_path.exists():
            raise RuntimeError("pending publication requires recovery")
        committed = root / "submitted.json"
        payload = json.dumps(job, sort_keys=True).encode()
        journal = {
            "schema": "floppylm.xbox.publication.v1",
            "kind": kind,
            "previous": json.loads(committed.read_text()) if committed.exists() else None,
            "candidate": {
                "job": job,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "package": self.package,
            },
        }
        self._durable_json(journal_path, journal)
        self._replay_publication(root, journal)
        self._ack_publication(root, journal)

    def _replay_publication(self, root: Path, journal: dict) -> None:
        job = journal["candidate"]["job"]
        original = json.loads((root / "job.json").read_text())
        for key in ("initialization", "data", "indices"):
            path = root / original[key]["path"]
            expected = job[key]
            if (
                path.stat().st_size != expected["bytes"]
                or runlog.sha256_file(path) != expected["sha256"]
            ):
                raise RuntimeError("publication asset integrity failed")
            if "chunks" in expected:
                with path.open("rb") as file:
                    for chunk in expected["chunks"]:
                        block = file.read(chunk["bytes"])
                        if hashlib.sha256(block).hexdigest() != chunk["sha256"]:
                            raise RuntimeError("publication chunk integrity failed")
                        self.upload(chunk["path"], block)
        self.upload(job["job_id"] + ".job.json", json.dumps(job, sort_keys=True).encode())
        if journal["kind"] == "resume":
            try:
                self.request("DELETE", self.path("file", "inbox", job["job_id"] + ".cancel"))
            except FileNotFoundError:
                pass
        self.upload(
            job["job_id"] + ".ready", b"resume" if journal["kind"] == "resume" else b"ready"
        )

    def _commit_publication(self, root: Path, journal: dict) -> None:
        self._durable_json(root / "submitted.json", journal["candidate"])
        (root / "publication.json").unlink()
        descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _ack_publication(self, root: Path, journal: dict) -> None:
        candidate = journal["candidate"]
        self.wait(
            candidate["job"]["job_id"], expected_sha=candidate["sha256"], acknowledgment_only=True
        )
        self._commit_publication(root, journal)

    def status(self, job_id: str) -> dict:
        return json.loads(self.get("status.json", "inbox/results/" + job_id))

    def wait(
        self,
        job_id: str,
        log=print,
        *,
        expected_sha: str | None = None,
        acknowledgment_only: bool = False,
    ) -> dict:
        previous = None
        transport_failures = 0
        deadline = time.monotonic() + 300
        acknowledged = False
        progress = time.monotonic()
        while True:
            if not acknowledged and time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Xbox acknowledgment timeout: job={job_id}, "
                    f"expected={expected_sha}, phase=status"
                )
            try:
                report = self.status(job_id)
            except FileNotFoundError:
                if acknowledged and time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Xbox status disappeared: job={job_id}, expected={expected_sha}"
                    )
                time.sleep(2)
                continue
            except (OSError, http.client.HTTPException) as error:
                transport_failures += 1
                log(
                    json.dumps(
                        {
                            "event": "transport_failure",
                            "attempt": transport_failures,
                            "error": type(error).__name__,
                        }
                    )
                )
                if transport_failures >= 5:
                    raise
                time.sleep(2**transport_failures)
                continue
            transport_failures = 0
            if expected_sha and report.get("job_sha256") != expected_sha:
                if report["state"] == "failed" or (acknowledged and time.monotonic() >= deadline):
                    raise RuntimeError(
                        f"Xbox status mismatch: expected={expected_sha}, "
                        f"observed={report.get('job_sha256')}, phase=status"
                    )
                time.sleep(2)
                continue
            acknowledged = True
            deadline = time.monotonic() + 300
            if acknowledgment_only:
                return report
            marker = (report["state"], report.get("trunk_step"))
            if marker != previous:
                log(
                    json.dumps(
                        {k: report[k] for k in ("state", "trunk_step", "last_loss") if k in report}
                    )
                )
                previous = marker
                progress = time.monotonic()
            elif time.monotonic() - progress >= 600:
                log(
                    json.dumps(
                        {
                            "event": "no_progress",
                            "job_id": job_id,
                            "expected_sha256": expected_sha,
                            "observed": marker,
                        }
                    )
                )
                progress = time.monotonic()
            if report["state"] != "running":
                return report
            time.sleep(2)

    def retrieve(self, descriptor: dict, path: Path) -> None:
        relative = Path(descriptor["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("artifact escapes job inbox")
        data = self.get(relative.name, "inbox/" + str(relative.parent))
        if (
            len(data) != descriptor["bytes"]
            or hashlib.sha256(data).hexdigest() != descriptor["sha256"]
        ):
            raise RuntimeError("downloaded artifact integrity failed")
        runlog.write_atomic(path, data)

    def cancel(self, job_id: str) -> None:
        self.upload(job_id + ".cancel", b"cancel")

    def fixture(self, initial: dict, job_id: str, *, timeout: float = 300) -> dict:
        self.upload(job_id + ".job.json", json.dumps(initial).encode())
        self.upload(job_id + ".ready", b"ready")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                return json.loads(self.get(job_id + ".actual.json"))
            except FileNotFoundError:
                try:
                    status = self.status(job_id)
                except FileNotFoundError:
                    status = {}
                if status.get("state") == "failed":
                    raise RuntimeError("Xbox fixture failed: " + status.get("error", "unknown"))
                time.sleep(2)
        raise TimeoutError("Xbox fixture did not finish")

    def recover(self, root: Path, *, purpose: str, acceptance: Path | None) -> dict:
        journal_path = root / "publication.json"
        journal = json.loads(journal_path.read_text()) if journal_path.exists() else None
        binding = (
            journal["candidate"] if journal else json.loads((root / "submitted.json").read_text())
        )
        job = binding["job"]
        if binding["package"] != self.package or job["purpose"] != purpose:
            raise RuntimeError("recovery package or purpose mismatch")
        if (
            hashlib.sha256(json.dumps(job, sort_keys=True).encode()).hexdigest()
            != binding["sha256"]
        ):
            raise RuntimeError("recovery submission hash mismatch")
        device = json.loads(self.get("device.json", ""))
        if device.get("package") != self.package or not device.get("hardware_gpu"):
            raise RuntimeError("recovery requires the original hardware package")
        if purpose == "scientific":
            if acceptance is None or runlog.sha256_file(acceptance) != job["acceptance_sha256"]:
                raise RuntimeError("recovery acceptance mismatch")
            check_acceptance(json.loads(acceptance.read_text()), device, self.package)
        original = json.loads((root / "job.json").read_text())
        for key in ("job_id", "config", "spec"):
            if original[key] != job[key]:
                raise RuntimeError("recovery recipe mismatch")
        for key in ("initialization", "data", "indices"):
            path = root / original[key]["path"]
            if (
                path.stat().st_size != job[key]["bytes"]
                or runlog.sha256_file(path) != job[key]["sha256"]
            ):
                raise RuntimeError("recovery asset integrity failed")
        if journal:
            if journal.get("schema") != "floppylm.xbox.publication.v1" or journal["kind"] not in (
                "submit",
                "resume",
            ):
                raise RuntimeError("unsupported publication journal")
            committed = root / "submitted.json"
            current = json.loads(committed.read_text()) if committed.exists() else None
            if current not in (journal["previous"], binding):
                raise RuntimeError("publication committed binding mismatch")
            try:
                pending_report = self.status(job["job_id"])
            except FileNotFoundError:
                pending_report = None
            if pending_report and pending_report.get("job_sha256") == binding["sha256"]:
                self._commit_publication(root, journal)
            else:
                previous = journal["previous"]
                if pending_report:
                    if not previous or pending_report.get("job_sha256") != previous["sha256"]:
                        raise RuntimeError("publication remote submission mismatch")
                    if pending_report["state"] not in ("interrupted", "completed"):
                        raise RuntimeError(
                            "publication replay requires a stopped previous execution"
                        )
                elif previous:
                    raise RuntimeError("publication cannot prove previous execution stopped")
                if journal["kind"] == "resume":
                    self.retrieve(job["resume"], root / "recovery-checkpoint.json")
                self._replay_publication(root, journal)
                self._ack_publication(root, journal)
        report = self.status(job["job_id"])
        if report.get("job_sha256") != binding["sha256"]:
            raise RuntimeError("recovery remote submission mismatch")
        if report["state"] == "interrupted":
            self.retrieve(report["checkpoint"], root / "recovery-checkpoint.json")
            history_path = root / "execution-segments.json"
            history = json.loads(history_path.read_text()) if history_path.exists() else []
            if not any(r["job_sha256"] == report["job_sha256"] for r in history):
                history.append(report)
                runlog.write_json(history_path, history)
            self.resume(root, report["checkpoint"])
        elif report["state"] not in ("running", "completed"):
            raise RuntimeError("failed jobs require diagnosis before recovery")
        return job

    def train(
        self,
        root: Path,
        model,
        spec,
        on_branch,
        *,
        purpose: str,
        acceptance: Path | None,
        recover: bool = False,
    ):
        from .jobs import restore_tensors

        submitted = (
            self.recover(root, purpose=purpose, acceptance=acceptance)
            if recover
            else self.submit(root, purpose=purpose, acceptance=acceptance)
        )
        job_id = submitted["job_id"]
        try:
            report = self.wait(
                job_id, expected_sha=json.loads((root / "submitted.json").read_text())["sha256"]
            )
        except KeyboardInterrupt:
            self.cancel(job_id)
            raise
        binding = json.loads((root / "submitted.json").read_text())
        if report.get("job_sha256") != binding["sha256"] or not report.get("hardware_gpu"):
            raise RuntimeError("Xbox result does not match submitted hardware job")
        if report["state"] != "completed" or len(report["branches"]) != 3:
            runlog.write_json(root / "result.json", report)
            raise RuntimeError("Xbox job did not complete: " + report["state"])
        history_path = root / "execution-segments.json"
        if history_path.exists():
            segments = json.loads(history_path.read_text()) + [dict(report)]
            for key in ("wall_seconds", "gpu_seconds", "dispatches", "transfer_bytes"):
                report[key] = sum(segment[key] for segment in segments)
            report["peak_memory_bytes"] = max(segment["peak_memory_bytes"] for segment in segments)
            report["execution_segments"] = segments
        runlog.write_json(root / "result.json", report)
        for branch in sorted(report["branches"], key=lambda b: b["end_step"]):
            path = root / ("branch-" + str(branch["end_step"]) + ".json")
            self.retrieve(branch["artifact"], path)
            weights = json.loads(path.read_text())
            if (
                weights["schema"] != "floppylm.e0.weights.v1"
                or weights["config"] != model.cfg.to_dict()
            ):
                raise RuntimeError("Xbox weights config mismatch")
            restore_tensors(model, weights["tensors"])
            on_branch(branch["end_step"], model, branch)
        return {
            "trunk_tokens": report["trunk_step"] * spec.batch * model.cfg.ctx,
            "trunk_seconds": report["wall_seconds"]
            - sum(b["cooldown_seconds"] for b in report["branches"]),
            "cooldowns": report["branches"],
            "backend": report,
        }

    def resume(self, root: Path, checkpoint: dict) -> str:
        binding = json.loads((root / "submitted.json").read_text())
        if binding["package"] != self.package:
            raise RuntimeError("resume package mismatch")
        job = binding["job"]
        previous = self.status(job["job_id"])
        if previous.get("job_sha256") != binding["sha256"]:
            raise RuntimeError("resume remote submission mismatch")
        if previous.get("state") != "interrupted" or previous.get("checkpoint") != checkpoint:
            raise RuntimeError("resume requires the bound interrupted checkpoint")
        job.pop("stop_after", None)
        job["resume"] = checkpoint
        self._publish(root, job, "resume")
        return hashlib.sha256(json.dumps(job, sort_keys=True).encode()).hexdigest()
