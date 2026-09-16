from pathlib import Path
import hashlib, json

from tools.runtime.dependency_lock import build_dependency_lock, fingerprint, verify_lock_hash
from tools.runtime.adapter_registry import AdapterRegistry, RegisteredAdapter
from tools.runtime.trusted_host import TrustedHost
from tools.verification.execution_evidence_gate import evaluate_execution_evidence_gate


def test_dependency_lock_fingerprint_is_stable():
    lock = build_dependency_lock(lock_id="L1", adapter_id="mock", python={"implementation":"CPython","version":"3.12"}, packages=[{"name":"numpy","version":"1"}])
    assert lock["fingerprint"] == fingerprint(lock)
    assert verify_lock_hash(lock, lock["fingerprint"])


def test_registry_rejects_untrusted():
    r = AdapterRegistry()
    r.register(RegisteredAdapter("x", "CUSTOM", False, {"isolation": True, "network": False, "shell": False}))
    try:
        r.require_trusted("x")
        assert False
    except PermissionError:
        pass


def test_trusted_host_blocks_shell_and_network():
    r = AdapterRegistry()
    r.register(RegisteredAdapter("safe", "CUSTOM", True, {"isolation": True, "network": False, "shell": False}))
    assert TrustedHost(r).validate("safe")["trusted"] is True


def test_execution_evidence_missing_is_not_run(tmp_path: Path):
    report = evaluate_execution_evidence_gate(tmp_path, rebuild_dir=tmp_path / "rebuild")
    assert report["gate_decision"] == "NOT_RUN"


def test_execution_evidence_passes_when_hashes_match(tmp_path: Path):
    rebuild = tmp_path / "rebuild"
    rebuild.mkdir()
    lock = build_dependency_lock(lock_id="L1", adapter_id="safe", python={"implementation":"CPython","version":"3.12"})
    (rebuild / "dependency-lock.json").write_text(json.dumps(lock), encoding="utf-8")
    env = {"artifact_type":"EnvironmentClosure", "schema_version":"1.0-E", "fingerprint":"a" * 64}
    (rebuild / "environment-closure.json").write_text(json.dumps(env), encoding="utf-8")
    (rebuild / "result-bundle.json").write_text("result", encoding="utf-8")
    (rebuild / "execution.log").write_text("ok", encoding="utf-8")
    evidence = {"artifact_type":"ExecutionEvidence", "schema_version":"1.0-G", "execution_id":"e1", "execution_status":"SUCCESS", "adapter_id":"safe", "isolation_id":"iso1", "lock_hash":lock["fingerprint"], "environment_fingerprint":env["fingerprint"], "tool_ref":"mock", "input_hashes":[], "execution_log_hash":hashlib.sha256(b"ok").hexdigest(), "result_bundle_hash":hashlib.sha256(b"result").hexdigest(), "observed_at":"2026-01-01T00:00:00Z"}
    (rebuild / "execution-evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    assert evaluate_execution_evidence_gate(tmp_path, rebuild_dir=rebuild)["gate_decision"] == "PASS"
