"""V1.0-C reproducibility gate.

This module does not execute arbitrary code. It evaluates evidence produced by
an explicitly requested rebuild and compares it with the frozen run using
stable, deterministic contracts. A rebuild that was not actually produced
remains NOT_RUN; it is never inferred from the original result.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

PASS = "PASS"
FAIL = "FAIL"
NOT_RUN = "NOT_RUN"


def _read_json(path: Path) -> dict[str, Any] | None:
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
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _numbers_equal(a: Any, b: Any, atol: float, rtol: float) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not (math.isfinite(float(a)) and math.isfinite(float(b))):
            return a == b
        return abs(float(a) - float(b)) <= atol + rtol * abs(float(b))
    return a == b


def compare_result_bundles(reference: dict[str, Any], rebuilt: dict[str, Any], *, atol: float = 1e-8, rtol: float = 1e-6) -> list[dict[str, Any]]:
    """Compare identity, output values and metrics without mutating either bundle."""
    mismatches: list[dict[str, Any]] = []
    for key in ("model_id",):
        if reference.get(key) != rebuilt.get(key):
            mismatches.append({"kind": "field", "field": key, "reference": reference.get(key), "rebuilt": rebuilt.get(key)})

    ref_outputs = {str(x.get("name")): x for x in reference.get("outputs", []) if isinstance(x, dict)}
    new_outputs = {str(x.get("name")): x for x in rebuilt.get("outputs", []) if isinstance(x, dict)}
    if set(ref_outputs) != set(new_outputs):
        mismatches.append({"kind": "output_names", "reference": sorted(ref_outputs), "rebuilt": sorted(new_outputs)})
    for name in sorted(set(ref_outputs) & set(new_outputs)):
        rv, nv = ref_outputs[name].get("value"), new_outputs[name].get("value")
        if not _numbers_equal(rv, nv, atol, rtol):
            mismatches.append({"kind": "output_value", "name": name, "reference": rv, "rebuilt": nv})
        if ref_outputs[name].get("unit") != new_outputs[name].get("unit"):
            mismatches.append({"kind": "output_unit", "name": name, "reference": ref_outputs[name].get("unit"), "rebuilt": new_outputs[name].get("unit")})

    ref_metrics, new_metrics = reference.get("metrics", {}), rebuilt.get("metrics", {})
    if set(ref_metrics) != set(new_metrics):
        mismatches.append({"kind": "metric_names", "reference": sorted(ref_metrics), "rebuilt": sorted(new_metrics)})
    for name in sorted(set(ref_metrics) & set(new_metrics)):
        if not _numbers_equal(ref_metrics[name], new_metrics[name], atol, rtol):
            mismatches.append({"kind": "metric_value", "name": name, "reference": ref_metrics[name], "rebuilt": new_metrics[name]})
    return mismatches


def evaluate_reproducibility_gate(
    run_dir: str | Path,
    *,
    rebuild_dir: str | Path | None = None,
    required_source_paths: list[str] | None = None,
    atol: float = 1e-8,
    rtol: float = 1e-6,
) -> dict[str, Any]:
    root = Path(run_dir)
    checks: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []

    reference_result = _read_json(root / "result-bundle.json")
    submission = _read_json(root / "submission-manifest.json")
    checks.append({"check_id": "C01_REFERENCE_RESULT", "decision": PASS if reference_result else FAIL,
                   "message": "Frozen/reference ResultBundle exists."})
    checks.append({"check_id": "C02_SUBMISSION_MANIFEST", "decision": PASS if submission else NOT_RUN,
                   "message": "SubmissionManifest provides the reproducibility index."})

    if submission and required_source_paths:
        source_failures = []
        indexed = {str(x.get("path")): str(x.get("sha256")) for x in submission.get("artifacts", []) if isinstance(x, dict)}
        for rel in required_source_paths:
            path = root / rel
            expected = indexed.get(rel)
            if not path.is_file() or not expected:
                source_failures.append(rel)
            elif _sha256(path) != expected:
                source_failures.append(rel)
        checks.append({"check_id": "C03_SOURCE_HASHES", "decision": FAIL if source_failures else PASS,
                       "message": "Required source artifacts match recorded SHA256." if not source_failures else "Source artifact hash mismatch.",
                       "refs": source_failures})

    if rebuild_dir is None:
        checks.append({"check_id": "C04_REBUILD_EXECUTED", "decision": NOT_RUN,
                       "message": "No independently rebuilt run was supplied."})
    else:
        rebuild_root = Path(rebuild_dir)
        rebuilt_result = _read_json(rebuild_root / "result-bundle.json")
        if not rebuilt_result:
            checks.append({"check_id": "C04_REBUILD_EXECUTED", "decision": FAIL,
                           "message": "Rebuild directory supplied but ResultBundle is missing."})
        else:
            checks.append({"check_id": "C04_REBUILD_EXECUTED", "decision": PASS,
                           "message": "Independent rebuild ResultBundle exists."})
            if reference_result:
                mismatches = compare_result_bundles(reference_result, rebuilt_result, atol=atol, rtol=rtol)
                checks.append({"check_id": "C05_RESULT_REPRODUCIBILITY", "decision": FAIL if mismatches else PASS,
                               "message": "Rebuilt outputs/metrics match reference within tolerance." if not mismatches else "Rebuilt ResultBundle differs from reference.",
                               "refs": ["result-bundle.json", "rebuild/result-bundle.json"]})

    failures = [c["check_id"] for c in checks if c["decision"] == FAIL]
    not_run = [c["check_id"] for c in checks if c["decision"] == NOT_RUN]
    decision = FAIL if failures else (NOT_RUN if not_run else PASS)
    return {
        "artifact_type": "ReproducibilityGateReport",
        "schema_version": "1.0-C",
        "run_id": root.name,
        "rebuild_run_id": Path(rebuild_dir).name if rebuild_dir else None,
        "checks": checks,
        "mismatches": mismatches,
        "gate_decision": decision,
    }


def persist_reproducibility_gate(run_dir: str | Path, report: dict[str, Any]) -> Path:
    path = Path(run_dir) / "reproducibility-gate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path
