"""V0.9-E deterministic verification of ResultBundle/RunManifest.

Verification is intentionally conservative: it validates evidence that is
actually present and never upgrades a missing check to PASS.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def _finite(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    return True


def _check(check_id: str, category: str, status: str, evidence: str, metric: Any = None, threshold: Any = None, artifact_ref: str | None = None) -> dict[str, Any]:
    item = {"check_id": check_id, "category": category, "status": status, "evidence": evidence}
    if metric is not None:
        item["metric"] = metric
    if threshold is not None:
        item["threshold"] = threshold
    if artifact_ref:
        item["artifact_ref"] = artifact_ref
    return item


def verify_run(run_dir: str | Path, dispatch_item: dict[str, Any] | None = None) -> dict[str, Any]:
    run = Path(run_dir)
    manifest_path = run / "run-manifest.json"
    result_path = run / "result-bundle.json"
    checks: list[dict[str, Any]] = []

    if not manifest_path.exists():
        return _report("unknown", "MISSING", [_check("V-E01", "provenance", "FAIL", "run-manifest.json is missing")], "FAIL")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_id = str(manifest.get("run_id", "unknown"))

    if manifest.get("status") == "INPUT_BLOCKED":
        checks.append(_check("V-E01", "data", "FAIL", manifest.get("notes", "input blocked")))
        return _report(run_id, "INPUT_BLOCKED", checks, "FAIL")
    if manifest.get("status") != "RUN_COMPLETE" or not result_path.exists():
        checks.append(_check("V-E01", "provenance", "FAIL", f"run status={manifest.get('status')}; result bundle present={result_path.exists()}"))
        return _report(run_id, run_id, checks, "FAIL")

    result = json.loads(result_path.read_text(encoding="utf-8"))
    checks.append(_check("V-E01", "provenance", "PASS", "RunManifest and ResultBundle are present", artifact_ref=str(result_path)))
    checks.append(_check("V-E02", "numerical", "PASS" if result.get("status") == "VALIDATED" else "FAIL", f"ResultBundle status={result.get('status')}"))
    finite_ok = _finite(result.get("outputs", [])) and _finite(result.get("metrics", {}))
    checks.append(_check("V-E03", "numerical", "PASS" if finite_ok else "FAIL", "All numeric outputs and metrics are finite"))

    if dispatch_item is not None:
        expected = dispatch_item.get("model_id")
        actual = result.get("model_id")
        checks.append(_check("V-E04", "model", "PASS" if expected == actual else "FAIL", f"dispatch model={expected}; result model={actual}"))
        binding = dispatch_item.get("binding") or {}
        if binding.get("binding_status") == "BLOCKED":
            checks.append(_check("V-E05", "data", "FAIL", "dispatch binding is BLOCKED"))
        else:
            checks.append(_check("V-E05", "data", "PASS", "dispatch binding is not blocked"))

    # These require domain-specific evidence and are deliberately NOT inferred.
    checks.append(_check("V-E06", "sensitivity", "NOT_RUN", "Sensitivity evidence is not inferred from a single run"))
    checks.append(_check("V-E07", "robustness", "NOT_RUN", "Robustness evidence is not inferred from a single run"))

    if any(c["status"] == "FAIL" for c in checks):
        decision = "FAIL"
    elif any(c["status"] in {"WARN", "NOT_RUN"} for c in checks):
        decision = "PASS_WITH_WARNINGS"
    else:
        decision = "PASS"
    return _report(run_id, run_id, checks, decision)


def _report(run_id: str, task_or_status: str, checks: list[dict[str, Any]], decision: str) -> dict[str, Any]:
    return {
        "artifact_type": "VerificationReport",
        "schema_version": "0.9",
        "status": "VALIDATED" if decision != "FAIL" else "DRAFT",
        "run_id": run_id,
        "checks": checks,
        "gate_decision": decision,
        "critical_issues": [c["evidence"] for c in checks if c["status"] == "FAIL"],
        "recommendations": [c["evidence"] for c in checks if c["status"] == "NOT_RUN"],
    }


def persist_report(run_dir: str | Path, report: dict[str, Any]) -> Path:
    path = Path(run_dir) / "verification-report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
