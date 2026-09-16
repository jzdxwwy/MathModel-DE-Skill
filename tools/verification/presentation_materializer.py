"""V0.9-N deterministic presentation materialization.

PresentationDataManifest is the single source of truth for publishable
figure/table/equation payloads. This module resolves only declared bindings
against an authoritative ResultBundle and writes immutable, hashed payloads.
It deliberately does not draw pixels; renderers consume these payloads.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .rendered_consistency import _get_path, _hash_expression


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _resolve(result: dict[str, Any], path: str) -> Any:
    try:
        return _get_path(result, path)
    except KeyError:
        outputs = result.get("outputs", {}) or {}
        metrics = result.get("metrics", {}) or {}
        if isinstance(outputs, list):
            outputs = {str(x.get("name")): x.get("value") for x in outputs if isinstance(x, dict)}
        if path in outputs:
            return outputs[path]
        return _get_path(metrics, path)


def materialize_presentation(
    project_dir: str | Path,
    manifest: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    root = Path(project_dir)
    run_id = str(result.get("run_id") or "unknown-run")
    out_dir = root / "presentation" / "materialized" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    errors: list[str] = []
    source_manifest_sha256 = _sha256_bytes(_canonical_json(manifest))
    result_sha256 = _sha256_bytes(_canonical_json(result))

    for item in manifest.get("items", []) or []:
        item_run_id = item.get("run_id")
        if item_run_id is not None and str(item_run_id) != run_id:
            continue
        evidence_id = str(item.get("evidence_id", "unknown"))
        kind = str(item.get("kind", "unknown"))
        payload_bindings: list[dict[str, Any]] = []
        try:
            for binding in item.get("bindings", []) or []:
                path = str(binding.get("path") or binding.get("result_ref") or "")
                value = _resolve(result, path)
                payload = {
                    "source_ref": binding.get("source_ref"),
                    "result_ref": binding.get("result_ref"),
                    "path": path,
                    "value": value,
                }
                if binding.get("tolerance") is not None:
                    payload["tolerance"] = binding["tolerance"]
                if binding.get("normalized_expression") is not None:
                    expr = str(binding["normalized_expression"])
                    payload["normalized_expression"] = expr
                    payload["expression_hash"] = binding.get("expression_hash") or _hash_expression(expr)
                payload_bindings.append(payload)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"{evidence_id}: unresolved binding: {exc}")
            continue

        materialized = {
            "artifact_type": "MaterializedPresentationPayload",
            "schema_version": "0.9-N",
            "evidence_id": evidence_id,
            "kind": kind,
            "run_id": run_id,
            "source_manifest_sha256": source_manifest_sha256,
            "result_sha256": result_sha256,
            "render_ref": item.get("render_ref"),
            "bindings": payload_bindings,
        }
        data = (json.dumps(materialized, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        payload_path = out_dir / f"{evidence_id}.json"
        payload_path.write_bytes(data)
        payload_sha256 = _sha256_bytes(data)
        items.append({
            "evidence_id": evidence_id,
            "kind": kind,
            "render_ref": item.get("render_ref"),
            "payload_ref": str(payload_path.relative_to(root)),
            "payload_sha256": payload_sha256,
            "render_input_sha256": payload_sha256,
        })

    decision = "FAIL" if errors else ("NOT_RUN" if not items else "PASS")
    render_manifest = {
        "artifact_type": "PresentationRenderManifest",
        "schema_version": "0.9-N",
        "source_manifest_sha256": source_manifest_sha256,
        "result_run_id": result.get("run_id"),
        "result_sha256": result_sha256,
        "items": items,
        "errors": errors,
        "gate_decision": decision,
    }
    manifest_path = root / "runs" / run_id / "presentation-render-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(render_manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return render_manifest
