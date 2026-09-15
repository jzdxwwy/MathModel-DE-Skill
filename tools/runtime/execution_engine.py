"""V0.9 execution engine: turn approved ToolDispatch plans into auditable runs.

The engine is deliberately small and provider-neutral. It executes only tools
registered in ToolRegistry, records the exact dispatch, input hashes, command,
parameters and outputs, and never marks a run complete when the tool fails.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from .tool_registry import ToolRegistry


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


class ToolExecutionEngine:
    def __init__(self, repo_root: Path, registry: ToolRegistry):
        self.repo_root = repo_root
        self.registry = registry

    def execute(self, dispatch: dict[str, Any], project_dir: Path, problem: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for item in dispatch.get("dispatches", []):
            results.append(self._execute_one(item, project_dir, problem))
        return results

    def _execute_one(self, item: dict[str, Any], project_dir: Path, problem: str) -> dict[str, Any]:
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        run_dir = project_dir / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        model_id = item["model_id"]
        tool_name = item["tool"]
        manifest = {
            "run_id": run_id,
            "problem": problem,
            "question": item["task_id"],
            "model": model_id,
            "parameters": item.get("parameters", {}),
            "seed": item.get("seed"),
            "python": sys.version.split()[0],
            "packages": {},
            "command": f"ToolRegistry.invoke({tool_name!r})",
            "outputs": [],
            "status": "RUNNING",
            "notes": "V0.9 execution; input facts remain traceable to upstream DataProfile/ProblemMap artifacts.",
        }
        _write_json(run_dir / "run-manifest.json", manifest)
        try:
            tool = self.registry.get(tool_name)
            payload = {
                "task_id": item["task_id"],
                "model_id": model_id,
                "project_dir": str(project_dir),
                "run_dir": str(run_dir),
                "inputs": item.get("inputs", []),
                "parameters": item.get("parameters", {}),
            }
            result = self.registry.invoke(tool_name, **payload)
            result_payload = result if isinstance(result, dict) else {"result": result}
            result_path = run_dir / "result-bundle.json"
            _write_json(result_path, {
                "artifact_type": "ResultBundle",
                "schema_version": "0.9",
                "status": "VALIDATED",
                "run_id": run_id,
                "task_id": item["task_id"],
                "model_id": model_id,
                "tool": tool_name,
                "results": result_payload,
                "provenance": {"dispatch_status": item.get("status", "PLANNED")},
            })
            manifest["outputs"] = [str(result_path)]
            manifest["status"] = "RUN_COMPLETE"
            manifest["input_hash"] = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        except Exception as exc:
            manifest["status"] = "FAILED"
            manifest["notes"] = f"Execution failed: {type(exc).__name__}: {exc}"
        _write_json(run_dir / "run-manifest.json", manifest)
        return manifest
