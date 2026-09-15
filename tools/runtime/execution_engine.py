"""V0.9 execution engine: approved dispatch -> auditable ResultBundle."""
from __future__ import annotations
import hashlib
import json
import sys
import uuid
from pathlib import Path
from typing import Any
from .template_adapter import InputBlocked
from .tool_registry import ToolRegistry


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


class ToolExecutionEngine:
    def __init__(self, repo_root: Path, registry: ToolRegistry):
        self.repo_root = repo_root
        self.registry = registry

    def execute(self, dispatch: dict[str, Any], project_dir: Path, problem: str) -> list[dict[str, Any]]:
        return [self._execute_one(item, project_dir, problem) for item in dispatch.get("dispatches", [])]

    def _execute_one(self, item: dict[str, Any], project_dir: Path, problem: str) -> dict[str, Any]:
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        run_dir = project_dir / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        model_id = item["model_id"]
        tool_name = item["tool"]
        binding = item.get("binding") or item.get("parameters") or {}
        manifest = {
            "run_id": run_id, "problem": problem, "question": item["task_id"],
            "model": model_id, "parameters": item.get("parameters", {}),
            "binding": binding, "seed": item.get("seed"), "python": sys.version.split()[0],
            "packages": {}, "command": f"ToolRegistry.invoke({tool_name!r})",
            "outputs": [], "status": "RUNNING", "notes": "V0.9-D; binding gate is authoritative.",
        }
        _write_json(run_dir / "run-manifest.json", manifest)
        if item.get("status") == "BLOCKED" or binding.get("binding_status") == "BLOCKED":
            manifest["status"] = "INPUT_BLOCKED"
            manifest["notes"] = f"Binding gate blocked: {binding.get('reason', 'missing or ambiguous input binding')}"
            _write_json(run_dir / "run-manifest.json", manifest)
            return manifest
        try:
            self.registry.get(tool_name)
            payload = {
                "task_id": item["task_id"], "model_id": model_id,
                "project_dir": str(project_dir), "run_dir": str(run_dir),
                "repo_root": str(self.repo_root), "inputs": item.get("inputs", []),
                "parameters": item.get("parameters", {}), "binding": binding,
            }
            result = self.registry.invoke(tool_name, **payload)
            result_payload = result if isinstance(result, dict) else {"result": result}
            result_path = run_dir / "result-bundle.json"
            outputs = result_payload.get("outputs", [{"name": "execution", "value": "completed", "unit": "status"}])
            artifacts = result_payload.get("artifacts", [])
            bundle = {
                "artifact_type": "ResultBundle", "schema_version": "0.9",
                "status": "VALIDATED", "run_id": run_id, "model_id": model_id,
                "outputs": outputs, "metrics": result_payload.get("metrics", {}),
                "artifacts": artifacts, "warnings": [],
                "provenance": {"input_refs": item.get("inputs", []), "code_ref": tool_name, "environment": sys.version.split()[0]},
            }
            _write_json(result_path, bundle)
            manifest["outputs"] = [str(result_path)]
            manifest["status"] = "RUN_COMPLETE"
            manifest["input_hash"] = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        except InputBlocked as exc:
            manifest["status"] = "INPUT_BLOCKED"
            manifest["notes"] = f"Input blocked: {exc}"
        except Exception as exc:
            manifest["status"] = "FAILED"
            manifest["notes"] = f"Execution failed: {type(exc).__name__}: {exc}"
        _write_json(run_dir / "run-manifest.json", manifest)
        return manifest
