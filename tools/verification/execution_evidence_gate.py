"""V1.0-G gate for observed trusted-host execution evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"


def _read(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def evaluate_execution_evidence_gate(run_dir: str | Path, *, rebuild_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(run_dir)
    evidence_root = Path(rebuild_dir) if rebuild_dir else None
    if evidence_root is None:
        return {"artifact_type": "ExecutionEvidenceGateReport", "schema_version": "1.0-G", "gate_decision": NOT_RUN,
                "reason": "trusted-host execution evidence directory not supplied"}
    evidence = _read(evidence_root / "execution-evidence.json")
    if evidence is None:
        return {"artifact_type": "ExecutionEvidenceGateReport", "schema_version": "1.0-G", "gate_decision": NOT_RUN,
                "reason": "execution evidence missing"}
    failures: list[str] = []
    if evidence.get("execution_status") != "SUCCESS":
        failures.append("execution_status")
    lock = _read(evidence_root / "dependency-lock.json")
    if lock is None or lock.get("fingerprint") != evidence.get("lock_hash"):
        failures.append("lock_hash")
    env = _read(evidence_root / "environment-closure.json")
    if env is None or env.get("fingerprint") != evidence.get("environment_fingerprint"):
        failures.append("environment_fingerprint")
    result_path = evidence_root / "result-bundle.json"
    if not result_path.is_file() or _sha256(result_path) != evidence.get("result_bundle_hash"):
        failures.append("result_bundle_hash")
    log_path = evidence_root / "execution.log"
    if not log_path.is_file() or _sha256(log_path) != evidence.get("execution_log_hash"):
        failures.append("execution_log_hash")
    if not evidence.get("adapter_id") or not evidence.get("isolation_id"):
        failures.append("execution_identity")
    return {"artifact_type": "ExecutionEvidenceGateReport", "schema_version": "1.0-G",
            "run_id": root.name, "rebuild_run_id": evidence_root.name,
            "gate_decision": FAIL if failures else PASS, "failures": failures,
            "evidence_ref": "execution-evidence.json"}


def persist_execution_evidence_gate(run_dir: str | Path, report: dict[str, Any]) -> Path:
    path = Path(run_dir) / "execution-evidence-gate.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path
