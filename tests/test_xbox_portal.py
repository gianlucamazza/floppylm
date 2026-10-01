"""Transport invariants: content binding, package provenance and stale resume state."""

import hashlib
import json
from unittest.mock import Mock

import pytest

from floppylm_xbox.portal import (
    CREDENTIAL_KEYS,
    Portal,
    certificate_fingerprint,
    package_matches,
    read_env_file,
)

PIN = "ab" * 32


def portal():
    return Portal("https://127.0.0.1:11443", "test", "test", "test-package", cert_sha256=PIN)


def test_asset_chunks_reused_and_download_hash_verified(tmp_path):
    client = portal()
    client.upload = Mock()
    source = tmp_path / "data.bin"
    source.write_bytes(b"corpus")
    digest = hashlib.sha256(b"corpus").hexdigest()
    descriptor = client.asset(source, {digest + ".chunk": 6})
    client.upload.assert_not_called()
    assert descriptor["chunks"][0]["sha256"] == digest
    client.get = Mock(return_value=b"changed")
    with pytest.raises(RuntimeError, match="integrity"):
        client.retrieve(descriptor, tmp_path / "result")
    assert not (tmp_path / "result").exists()


def test_scientific_submit_rejects_different_source_commit(tmp_path):
    client = portal()
    client.get = Mock(
        return_value=json.dumps(
            {
                "state": "ready",
                "hardware_gpu": True,
                "package": client.package,
                "commit": "new",
            }
        ).encode()
    )
    proof = tmp_path / "acceptance.json"
    proof.write_text(
        json.dumps(
            {
                "schema": "floppylm_xbox.jobs.acceptance.v1",
                "ok": True,
                "package": client.package,
                "commit": "old",
                "kernels": {"ok": True},
            }
        )
    )
    with pytest.raises(RuntimeError, match="source commit"):
        client.submit(tmp_path, purpose="scientific", acceptance=proof)


def test_resume_wait_ignores_previous_interrupted_status(monkeypatch):
    client = portal()
    client.status = Mock(
        side_effect=[
            {"state": "interrupted", "job_sha256": "old"},
            {"state": "running", "job_sha256": "new", "trunk_step": 9},
            {"state": "completed", "job_sha256": "new", "trunk_step": 29},
        ]
    )
    monkeypatch.setattr("floppylm_xbox.portal.time.sleep", lambda _: None)
    assert client.wait("job", log=lambda _: None, expected_sha="new")["state"] == "completed"


def test_remote_artifact_cannot_escape_inbox(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        portal().retrieve({"path": "../private", "bytes": 1, "sha256": "unused"}, tmp_path / "out")


def clear_portal_env(monkeypatch):
    for key in (*CREDENTIAL_KEYS, "XBOX_PORT", "XGPU_E0_PACKAGE", "FLOPPYLM_XBOX_ENV"):
        monkeypatch.delenv(key, raising=False)


def test_env_file_is_parsed_without_a_shell(tmp_path, monkeypatch):
    clear_portal_env(monkeypatch)
    config = tmp_path / ".config/floppylm/xbox.env"
    config.parent.mkdir(parents=True)
    config.write_text(
        "# Device Portal\nexport XBOX_IP=127.0.0.1\nXBOX_PORT=12000\n"
        f"XBOX_USER=test\nXBOX_PASS='test $literal' # comment\nXBOX_CERT_SHA256={PIN}\n"
    )
    monkeypatch.setattr("floppylm_xbox.portal.Path.home", lambda: tmp_path)
    client = Portal.configured(package="known")
    assert (client.host, client.port, client.package) == ("127.0.0.1", 12000, "known")
    assert read_env_file(config)["XBOX_PASS"] == "test $literal"


def test_environment_overrides_env_file(tmp_path, monkeypatch):
    clear_portal_env(monkeypatch)
    config = tmp_path / "xbox.env"
    config.write_text(f"XBOX_IP=10.0.0.1\nXBOX_USER=file\nXBOX_PASS=file\nXBOX_CERT_SHA256={PIN}\n")
    monkeypatch.setenv("FLOPPYLM_XBOX_ENV", str(config))
    monkeypatch.setenv("XBOX_IP", "127.0.0.2")
    client = Portal.configured(package="known")
    assert (client.host, client.port) == ("127.0.0.2", 11443)


def test_missing_settings_name_the_keys(tmp_path, monkeypatch):
    clear_portal_env(monkeypatch)
    monkeypatch.setattr("floppylm_xbox.portal.Path.home", lambda: tmp_path)
    with pytest.raises(RuntimeError, match="XBOX_IP, XBOX_USER, XBOX_PASS, XBOX_CERT_SHA256"):
        Portal.configured(package="known")


def test_certificate_fingerprint_normalization():
    assert certificate_fingerprint(":".join(["AB"] * 32)) == PIN
    with pytest.raises(ValueError):
        certificate_fingerprint("ab" * 31)
    with pytest.raises(ValueError):
        certificate_fingerprint("zz" * 32)


@pytest.fixture
def tls_server(tmp_path):
    """Local HTTPS server with a fresh self-signed certificate, like Device Portal."""
    import datetime
    import http.server
    import ssl
    import threading

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "device-portal")])
    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(hours=1))
        .sign(key, hashes.SHA256())
    )
    (tmp_path / "cert.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    (tmp_path / "key.pem").write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    seen = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.headers.get("Authorization"))
            body = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(tmp_path / "cert.pem", tmp_path / "key.pem")
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    fingerprint = hashlib.sha256(cert.public_bytes(serialization.Encoding.DER)).hexdigest()
    yield f"https://127.0.0.1:{server.server_address[1]}", fingerprint, seen
    server.shutdown()
    server.server_close()


def test_pinned_certificate_is_accepted(tls_server):
    url, fingerprint, seen = tls_server
    client = Portal(url, "user", "secret", "pkg", cert_sha256=fingerprint)
    assert client.request("GET", "/", json_result=True) == {"ok": True}
    assert len(seen) == 1


def test_unpinned_certificate_is_rejected_before_sending_credentials(tls_server):
    import ssl

    url, _, seen = tls_server
    client = Portal(url, "user", "secret", "pkg", cert_sha256="cd" * 32)
    with pytest.raises(ssl.SSLCertVerificationError, match="XBOX_CERT_SHA256"):
        client.request("GET", "/")
    assert seen == []


def test_package_discovery_ignores_publisher():
    assert package_matches("Someone.XgpuE0_0.1.0.28_x64__abc", "XgpuE0")
    assert package_matches("XgpuE0_0.1.0.28_x64__abc", "XgpuE0")
    assert not package_matches("Someone.XgpuE0Old_0.1_x64__abc", "XgpuE0")


def recovery_job(tmp_path, client, state):
    job = {
        "job_id": "recovery",
        "purpose": "functional",
        "config": {},
        "spec": {},
    }
    original = dict(job)
    for key in ("initialization", "data", "indices"):
        p = tmp_path / (key + ".bin")
        p.write_bytes(key.encode())
        descriptor = {
            "path": p.name,
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        job[key] = descriptor
        original[key] = descriptor
    digest = hashlib.sha256(json.dumps(job, sort_keys=True).encode()).hexdigest()
    (tmp_path / "job.json").write_text(json.dumps(original))
    (tmp_path / "submitted.json").write_text(
        json.dumps({"package": client.package, "job": job, "sha256": digest})
    )
    client.get = Mock(
        return_value=json.dumps({"package": client.package, "hardware_gpu": True}).encode()
    )
    report = {
        "state": state,
        "job_sha256": digest,
        "checkpoint": {"path": "results/recovery/checkpoint.json"},
    }
    client.status = Mock(return_value=report)
    client.submit = Mock()
    client.resume = Mock()
    client.retrieve = Mock()
    return report


@pytest.mark.parametrize("state", ["running", "completed"])
def test_recovery_reuses_bound_job_without_resubmission(tmp_path, state):
    client = portal()
    recovery_job(tmp_path, client, state)
    assert client.recover(tmp_path, purpose="functional", acceptance=None)["job_id"] == "recovery"
    client.resume.assert_not_called()
    client.submit.assert_not_called()


def test_recovery_interruption_verifies_checkpoint_before_resume(tmp_path):
    client = portal()
    report = recovery_job(tmp_path, client, "interrupted")
    client.recover(tmp_path, purpose="functional", acceptance=None)
    client.retrieve.assert_called_once_with(
        report["checkpoint"], tmp_path / "recovery-checkpoint.json"
    )
    client.resume.assert_called_once_with(tmp_path, report["checkpoint"])


def test_recovery_rejects_changed_asset_and_failed_remote_job(tmp_path):
    client = portal()
    recovery_job(tmp_path, client, "failed")
    with pytest.raises(RuntimeError, match="diagnosis"):
        client.recover(tmp_path, purpose="functional", acceptance=None)
    (tmp_path / "data.bin").write_bytes(b"changed")
    with pytest.raises(RuntimeError, match="integrity"):
        client.recover(tmp_path, purpose="functional", acceptance=None)


def test_wait_records_transport_loss_without_cancel(monkeypatch):
    client = portal()
    client.status = Mock(
        side_effect=[OSError("offline"), {"state": "completed", "job_sha256": "same"}]
    )
    client.cancel = Mock()
    log = Mock()
    monkeypatch.setattr("floppylm_xbox.portal.time.sleep", lambda _: None)
    assert client.wait("job", log=log, expected_sha="same")["state"] == "completed"
    assert "transport_failure" in log.call_args_list[0].args[0]
    client.cancel.assert_not_called()
