"""V1.0-V4.1 benchmark readiness harness.

This module validates benchmark input readiness and never invents historical
attachments or solves the benchmark problem.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_input_manifest(benchmark_id: str, attachments: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    for item in attachments:
        path = Path(item["path"])
        if path.is_file():
            items.append({
                "attachment_id": item["attachment_id"],
                "required": bool(item.get("required", True)),
                "status": "PRESENT",
                "path": str(path),
                "sha256": sha256_file(path),
                "media_type": item.get("media_type", "application/octet-stream"),
            })
        else:
            items.append({
                "attachment_id": item["attachment_id"],
                "required": bool(item.get("required", True)),
                "status": "MISSING",
                "path": str(path),
            })
    return {
        "artifact_type": "BenchmarkInputManifest",
        "schema_version": "1.0",
        "benchmark_id": benchmark_id,
        "attachments": items,
    }


def evaluate_benchmark_readiness(manifest: dict[str, Any]) -> dict[str, Any]:
    missing = [
        item["attachment_id"]
        for item in manifest["attachments"]
        if item["required"] and item["status"] != "PRESENT"
    ]
    if missing:
        status = "BLOCKED"
        stage_status = "BLOCKED"
        message = "Required benchmark attachments are missing."
    else:
        status = "READY"
        stage_status = "READY"
        message = "Required benchmark attachments are present."

    return {
        "artifact_type": "BenchmarkRun",
        "schema_version": "1.0",
        "benchmark_id": manifest["benchmark_id"],
        "status": status,
        "input_manifest_ref": "benchmark-input-manifest.json",
        "run_id": None,
        "stages": [{
            "stage_id": "B01_INPUT_READINESS",
            "status": stage_status,
            "message": message,
            "input_refs": missing or [item["attachment_id"] for item in manifest["attachments"]],
            "output_refs": [],
        }],
        "gate_decision": "NOT_RUN",
    }


def run_readiness_check(
    run_dir: str | Path,
    benchmark_id: str,
    attachments: list[dict[str, Any]],
) -> dict[str, Any]:
    root = Path(run_dir)
    root.mkdir(parents=True, exist_ok=True)
    manifest = build_input_manifest(benchmark_id, attachments)
    (root / "benchmark-input-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    result = evaluate_benchmark_readiness(manifest)
    (root / "benchmark-run.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result
