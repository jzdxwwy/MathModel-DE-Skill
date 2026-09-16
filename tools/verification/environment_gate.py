"""V1.0-E environment closure gate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..runtime.environment_closure import fingerprint_closure

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"


def _read(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _compare(a: Any, b: Any, prefix: str = "") -> list[str]:
    mismatches: list[str] = []
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                mismatches.append(f"{prefix}{key}: missing")
            else:
                mismatches.extend(_compare(a[key], b[key], f"{prefix}{key}."))
    elif isinstance(a, list) and isinstance(b, list):
        if a != b:
            mismatches.append(f"{prefix[:-1] if prefix else prefix}: list differs")
    elif a != b:
        mismatches.append(f"{prefix[:-1] if prefix else prefix}: {a!r} != {b!r}")
    return mismatches


def evaluate_environment_gate(run_dir: str | Path, rebuild_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(run_dir)
    rebuild = Path(rebuild_dir) if rebuild_dir else None
    reference = _read(root / "environment-closure.json")
    rebuilt = _read(rebuild / "environment-closure.json") if rebuild else None
    checks = []
    mismatches: list[str] = []

    if reference is None:
        checks.append({"check_id": "E01_REFERENCE_CLOSURE", "decision": NOT_RUN, "message": "Reference EnvironmentClosure missing."})
        return _report(root.name, reference, rebuilt, checks, mismatches)
    if not reference.get("complete", False):
        checks.append({"check_id": "E01_REFERENCE_CLOSURE", "decision": NOT_RUN, "message": "Reference environment closure is incomplete."})
    else:
        checks.append({"check_id": "E01_REFERENCE_CLOSURE", "decision": PASS, "message": "Complete reference closure present."})

    stored_ref_fp = str(reference.get("fingerprint", ""))
    computed_ref_fp = fingerprint_closure(reference)
    checks.append({"check_id": "E02_REFERENCE_FINGERPRINT", "decision": PASS if stored_ref_fp == computed_ref_fp else FAIL,
                   "message": "Reference fingerprint is self-consistent." if stored_ref_fp == computed_ref_fp else "Reference fingerprint mismatch."})

    if rebuilt is None:
        checks.append({"check_id": "E03_REBUILD_CLOSURE", "decision": NOT_RUN, "message": "Rebuild EnvironmentClosure missing."})
        return _report(root.name, reference, rebuilt, checks, mismatches)
    if not rebuilt.get("complete", False):
        checks.append({"check_id": "E03_REBUILD_CLOSURE", "decision": NOT_RUN, "message": "Rebuild environment closure is incomplete."})
    else:
        checks.append({"check_id": "E03_REBUILD_CLOSURE", "decision": PASS, "message": "Complete rebuild closure present."})

    stored_rebuild_fp = str(rebuilt.get("fingerprint", ""))
    computed_rebuild_fp = fingerprint_closure(rebuilt)
    checks.append({"check_id": "E04_REBUILD_FINGERPRINT", "decision": PASS if stored_rebuild_fp == computed_rebuild_fp else FAIL,
                   "message": "Rebuild fingerprint is self-consistent." if stored_rebuild_fp == computed_rebuild_fp else "Rebuild fingerprint mismatch."})

    if reference.get("complete") and rebuilt.get("complete"):
        mismatches = _compare({k: v for k, v in reference.items() if k not in {"fingerprint", "run_id"}},
                              {k: v for k, v in rebuilt.items() if k not in {"fingerprint", "run_id"}})
        checks.append({"check_id": "E05_CLOSURE_MATCH", "decision": PASS if not mismatches else FAIL,
                       "message": "Reference and rebuild closures match." if not mismatches else "Environment closure mismatch detected."})
    else:
        checks.append({"check_id": "E05_CLOSURE_MATCH", "decision": NOT_RUN, "message": "Closure comparison requires complete closures."})
    return _report(root.name, reference, rebuilt, checks, mismatches)


def _report(run_id: str, reference: dict[str, Any] | None, rebuilt: dict[str, Any] | None, checks: list[dict[str, Any]], mismatches: list[str]) -> dict[str, Any]:
    decisions = [c["decision"] for c in checks]
    decision = FAIL if FAIL in decisions else (NOT_RUN if NOT_RUN in decisions else PASS)
    return {"artifact_type": "EnvironmentGateReport", "schema_version": "1.0-E", "run_id": run_id,
            "reference_fingerprint": reference.get("fingerprint") if reference else None,
            "rebuild_fingerprint": rebuilt.get("fingerprint") if rebuilt else None,
            "checks": checks, "mismatches": mismatches, "gate_decision": decision}


def persist_environment_gate(run_dir: str | Path, report: dict[str, Any]) -> Path:
    path = Path(run_dir) / "environment-gate.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path
