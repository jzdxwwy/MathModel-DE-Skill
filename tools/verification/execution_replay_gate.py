"""V1.0-H execution replay evidence gate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"


def _read(path: Path) -> dict[str, Any] | None:
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


def evaluate_execution_replay_gate(run_dir: str | Path) -> dict[str, Any]:
    root = Path(run_dir)
    evidence = _read(root / "execution-replay-result.json")
    result = root / "result-bundle.json"
    log = root / "execution-log.json"
    if evidence is None:
        return {"artifact_type": "ExecutionReplayGateReport", "schema_version": "1.0-H",
                "gate_decision": NOT_RUN, "reasons": ["execution replay evidence missing"]}
    reasons: list[str] = []
    if evidence.get("status") != "EXECUTED": reasons.append("execution status is not EXECUTED")
    if not result.is_file(): reasons.append("result-bundle.json missing")
    elif evidence.get("result_bundle_sha256") != _sha256(result): reasons.append("result bundle hash mismatch")
    if not log.is_file(): reasons.append("execution-log.json missing")
    elif evidence.get("execution_log_sha256") != _sha256(log): reasons.append("execution log hash mismatch")
    if not evidence.get("adapter_id") or not evidence.get("tool"): reasons.append("adapter/tool identity missing")
    if not evidence.get("isolation_id"): reasons.append("isolation identity missing")
    if not evidence.get("lock_hash"): reasons.append("dependency lock hash missing")
    if not evidence.get("environment_fingerprint"): reasons.append("environment fingerprint missing")
    decision = FAIL if reasons else PASS
    return {"artifact_type": "ExecutionReplayGateReport", "schema_version": "1.0-H",
            "gate_decision": decision, "reasons": reasons,
            "evidence_ref": "execution-replay-result.json"}
