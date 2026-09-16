"""V1.0-I gate for concrete Python venv materialization evidence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def evaluate_materialization_gate(run_dir: str | Path) -> dict[str, Any]:
    root = Path(run_dir)
    evidence_path = root / "venv-materialization-evidence.json"
    if not evidence_path.is_file():
        return {"artifact_type": "MaterializationGateReport", "schema_version": "1.0-I", "gate_decision": "NOT_RUN", "reasons": ["missing venv-materialization-evidence.json"]}
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"artifact_type": "MaterializationGateReport", "schema_version": "1.0-I", "gate_decision": "FAIL", "reasons": [f"invalid evidence JSON: {exc}"]}

    reasons: list[str] = []
    if evidence.get("status") != "MATERIALIZED":
        reasons.append("materialization status is not MATERIALIZED")
    if evidence.get("fresh") is not True:
        reasons.append("materialization is not marked fresh")
    policy = evidence.get("policy", {})
    if policy.get("allow_network") is not False:
        reasons.append("network policy is not false")
    if policy.get("allow_shell") is not False:
        reasons.append("shell policy is not false")
    if policy.get("isolation_required") is not True:
        reasons.append("isolation_required is not true")
    interpreter = Path(str(evidence.get("interpreter", "")))
    if not interpreter.is_file():
        reasons.append("materialized interpreter does not exist")
    if not evidence.get("lock_hash"):
        reasons.append("missing dependency lock hash")
    if not evidence.get("interpreter_sha256"):
        reasons.append("missing interpreter hash")

    decision = "FAIL" if reasons else "PASS"
    return {
        "artifact_type": "MaterializationGateReport",
        "schema_version": "1.0-I",
        "materialization_id": evidence.get("materialization_id", ""),
        "gate_decision": decision,
        "reasons": reasons,
    }


def persist_materialization_evidence(evidence: dict[str, Any], run_dir: str | Path) -> Path:
    root = Path(run_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "venv-materialization-evidence.json"
    path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
