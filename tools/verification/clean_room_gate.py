"""V1.0-F Clean-Room Execution Evidence Gate."""
from __future__ import annotations
from pathlib import Path
import json
from typing import Any

from tools.runtime.environment_closure import fingerprint_closure

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"


def _read(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def evaluate_clean_room_gate(reference_run_dir: str | Path, rebuild_run_dir: str | Path | None = None) -> dict[str, Any]:
    ref = Path(reference_run_dir)
    reference = _read(ref / "environment-closure.json")
    if reference is None:
        return {"artifact_type": "CleanRoomGateReport", "schema_version": "1.0-F",
                "decision": NOT_RUN, "checks": [{"id": "F01_REFERENCE_ENV", "decision": NOT_RUN}]}
    if rebuild_run_dir is None:
        return {"artifact_type": "CleanRoomGateReport", "schema_version": "1.0-F",
                "decision": NOT_RUN, "checks": [{"id": "F02_REBUILD_ENV", "decision": NOT_RUN,
                                                    "message": "clean-room rebuild evidence not supplied"}]}
    observed_path = Path(rebuild_run_dir) / "environment-closure.json"
    observed = _read(observed_path)
    if observed is None:
        return {"artifact_type": "CleanRoomGateReport", "schema_version": "1.0-F",
                "decision": FAIL, "checks": [{"id": "F02_REBUILD_ENV", "decision": FAIL,
                                                 "message": "rebuild environment evidence missing"}]}

    mismatches = []
    reference_fingerprint = reference.get("fingerprint")
    observed_fingerprint = observed.get("fingerprint")
    recomputed_observed_fingerprint = fingerprint_closure(observed)
    if observed_fingerprint != recomputed_observed_fingerprint:
        mismatches.append("fingerprint_integrity")
    if reference_fingerprint != fingerprint_closure(reference):
        mismatches.append("reference_fingerprint_integrity")

    for key in ("python", "platform", "packages", "tools", "source_files", "inputs", "model_refs", "spec_refs", "policy"):
        if reference.get(key) != observed.get(key):
            mismatches.append(key)
    decision = PASS if not mismatches else FAIL
    return {"artifact_type": "CleanRoomGateReport", "schema_version": "1.0-F",
            "decision": decision,
            "checks": [{"id": "F03_ENVIRONMENT_MATCH", "decision": decision, "mismatches": mismatches}]}
