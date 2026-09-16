"""V0.9-M deterministic consistency checks for rendered paper artifacts.

The verifier does not inspect pixels. It checks the deterministic presentation
manifest against authoritative ResultBundle/ModelSpec evidence before render.
"""
from __future__ import annotations

import hashlib
import math
from typing import Any


def _get_path(obj: Any, path: str) -> Any:
    cur = obj
    for part in path.split(".") if path else []:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            raise KeyError(path)
    return cur


def _equal(a: Any, b: Any, tol: float) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not (math.isfinite(float(a)) and math.isfinite(float(b))):
            return False
        return abs(float(a) - float(b)) <= tol + 1e-9 * max(1.0, abs(float(a)), abs(float(b)))
    return a == b


def _hash_expression(expr: str) -> str:
    return hashlib.sha256(" ".join(str(expr).split()).encode("utf-8")).hexdigest()


def verify_presentation_consistency(
    manifest: dict[str, Any],
    result: dict[str, Any],
    model_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    outputs = result.get("outputs", {}) or {}
    if isinstance(outputs, list):
        outputs = {str(x.get("name")): x.get("value") for x in outputs if isinstance(x, dict)}
    metrics = result.get("metrics", {}) or {}

    for item in manifest.get("items", []) or []:
        eid = str(item.get("evidence_id", "unknown"))
        kind = item.get("kind")
        for i, binding in enumerate(item.get("bindings", []) or []):
            source = binding.get("source_ref")
            ref = binding.get("result_ref")
            path = binding.get("path") or ref
            tol = float(binding.get("tolerance", 1e-8))
            try:
                try:
                    actual = _get_path(result, path)
                except KeyError:
                    actual = _get_path(outputs, path) if path in outputs else _get_path(metrics, path)
                expected = binding.get("value")
                if expected is None:
                    checks.append({"id": f"M-{kind}-{eid}-{i}", "status": "PASS", "message": f"{source} is bound to {ref}"})
                elif _equal(actual, expected, tol):
                    checks.append({"id": f"M-{kind}-{eid}-{i}", "status": "PASS", "message": f"{source} matches {ref}"})
                else:
                    checks.append({"id": f"M-{kind}-{eid}-{i}", "status": "FAIL", "message": f"{source} does not match {ref}: expected {expected!r}, got {actual!r}"})
            except (KeyError, TypeError, ValueError) as exc:
                checks.append({"id": f"M-{kind}-{eid}-{i}", "status": "FAIL", "message": f"unresolved result binding {ref}: {exc}"})

            if kind == "equation" and binding.get("normalized_expression") is not None:
                expr = str(binding["normalized_expression"])
                actual_hash = _hash_expression(expr)
                expected_hash = binding.get("expression_hash")
                status = "PASS" if not expected_hash or actual_hash == expected_hash else "FAIL"
                checks.append({"id": f"M-equation-hash-{eid}-{i}", "status": status, "message": "equation expression hash is consistent" if status == "PASS" else "equation expression hash mismatch"})

        if kind == "equation" and model_spec is not None:
            refs = item.get("model_refs", []) or []
            equations = model_spec.get("equations", []) or []
            ids = {str(x.get("id")) for x in equations if isinstance(x, dict) and x.get("id") is not None}
            for ref in refs:
                checks.append({"id": f"M-equation-ref-{eid}-{ref}", "status": "PASS" if str(ref) in ids else "FAIL", "message": "ModelSpec equation reference resolved" if str(ref) in ids else "unresolved ModelSpec equation reference"})

    decision = "FAIL" if any(c["status"] == "FAIL" for c in checks) else ("NOT_RUN" if not checks else "PASS")
    return {"artifact_type": "PresentationConsistencyReport", "schema_version": "0.9-M", "checks": checks, "gate_decision": decision}
