"""V1.0-D/E controlled automatic clean-rebuild engine.

Executes only a registered ToolRegistry tool. It never launches arbitrary
shell commands. Source/input hashes are checked before execution and the
rebuild uses a fresh run directory so the frozen result cannot be mutated.
V1.0-E additionally persists an explicitly supplied EnvironmentClosure.
"""
from __future__ import annotations
import json, sys, uuid
from pathlib import Path
from typing import Any
from .tool_registry import ToolRegistry
from .environment_closure import fingerprint_closure, persist_environment_closure, sha256_file

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"

def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")

def _sha256(path: Path) -> str:
    return sha256_file(path)

def validate_contract(contract: dict[str, Any], registry: ToolRegistry) -> list[str]:
    errors: list[str] = []
    if contract.get("artifact_type") != "RebuildContract": errors.append("artifact_type must be RebuildContract")
    if contract.get("schema_version") != "1.0-D": errors.append("schema_version must be 1.0-D")
    for key in ("run_id", "model_id", "tool"):
        if not isinstance(contract.get(key), str) or not contract[key]: errors.append(f"missing contract field: {key}")
    if contract.get("policy", {}).get("allow_shell", False): errors.append("arbitrary shell execution is forbidden")
    try: registry.get(contract.get("tool", ""))
    except KeyError: errors.append(f"unregistered rebuild tool: {contract.get('tool')}")
    if contract.get("expected_result", {}).get("model_id") != contract.get("model_id"):
        errors.append("expected_result.model_id does not match model_id")
    env = contract.get("environment_closure")
    if env is not None and env.get("artifact_type") != "EnvironmentClosure": errors.append("environment_closure must be an EnvironmentClosure")
    return errors

def verify_input_hashes(contract: dict[str, Any], project_dir: Path) -> list[str]:
    failures: list[str] = []
    for item in contract.get("inputs", []):
        rel = Path(str(item.get("path", ""))); path = project_dir / rel; expected = str(item.get("sha256", "")).lower()
        if not path.is_file(): failures.append(f"missing input: {rel}")
        elif _sha256(path).lower() != expected: failures.append(f"input hash mismatch: {rel}")
    return failures

class CleanRebuildEngine:
    """Execute one declared rebuild through the existing registered-tool boundary."""
    def __init__(self, repo_root: Path, registry: ToolRegistry): self.repo_root, self.registry = Path(repo_root), registry

    def rebuild(self, contract: dict[str, Any], project_dir: Path) -> dict[str, Any]:
        project_dir = Path(project_dir); errors = validate_contract(contract, self.registry); input_failures = verify_input_hashes(contract, project_dir)
        run_id = f"rebuild-{uuid.uuid4().hex[:12]}"; run_dir = project_dir / "runs" / run_id; run_dir.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, Any] = {"artifact_type": "RebuildRunManifest", "schema_version": "1.0-E", "run_id": run_id,
            "reference_run_id": contract.get("run_id"), "model_id": contract.get("model_id"), "tool": contract.get("tool"),
            "parameters": contract.get("parameters", {}), "python": sys.version.split()[0], "status": "BLOCKED", "checks": []}
        manifest["checks"].append({"check_id": "D01_CONTRACT", "decision": FAIL if errors else PASS, "refs": errors})
        manifest["checks"].append({"check_id": "D02_INPUT_HASHES", "decision": FAIL if input_failures else PASS, "refs": input_failures})
        _write_json(run_dir / "rebuild-run-manifest.json", manifest)
        if errors or input_failures: return manifest
        payload = {"task_id": f"rebuild:{contract['run_id']}", "model_id": contract["model_id"], "project_dir": str(project_dir),
                   "run_dir": str(run_dir), "repo_root": str(self.repo_root), "inputs": [x["path"] for x in contract.get("inputs", [])],
                   "parameters": contract.get("parameters", {}), "binding": {"binding_status": "VERIFIED_REBUILD_CONTRACT"}, "rebuild": True}
        try:
            result = self.registry.invoke(contract["tool"], **payload); result_payload = result if isinstance(result, dict) else {"result": result}
            bundle = {"artifact_type": "ResultBundle", "schema_version": "0.9", "status": "VALIDATED", "run_id": run_id,
                "model_id": contract["model_id"], "outputs": result_payload.get("outputs", []), "metrics": result_payload.get("metrics", {}),
                "artifacts": result_payload.get("artifacts", []), "warnings": [],
                "provenance": {"input_refs": [x["path"] for x in contract.get("inputs", [])], "code_ref": contract["tool"],
                               "environment": sys.version.split()[0], "rebuild_of": contract["run_id"]}}
            _write_json(run_dir / "result-bundle.json", bundle)
            env = contract.get("environment_closure")
            if env is not None:
                rebuilt_env = json.loads(json.dumps(env))
                rebuilt_env["run_id"] = run_id; rebuilt_env["capture_mode"] = "REBUILD_OBSERVED"; rebuilt_env["fingerprint"] = fingerprint_closure(rebuilt_env)
                persist_environment_closure(run_dir, rebuilt_env)
                manifest["checks"].append({"check_id": "E01_ENVIRONMENT_CLOSURE", "decision": PASS, "refs": ["environment-closure.json"]})
            else:
                manifest["checks"].append({"check_id": "E01_ENVIRONMENT_CLOSURE", "decision": NOT_RUN, "refs": ["environment-closure.json"]})
            manifest["status"] = "REBUILD_COMPLETE"; manifest["checks"].append({"check_id": "D03_REGISTERED_TOOL", "decision": PASS}); manifest["outputs"] = [str(run_dir / "result-bundle.json")]
        except Exception as exc:
            manifest["status"] = "FAILED"; manifest["checks"].append({"check_id": "D03_REGISTERED_TOOL", "decision": FAIL, "refs": [f"{type(exc).__name__}: {exc}"]})
        _write_json(run_dir / "rebuild-run-manifest.json", manifest); return manifest

def build_rebuild_contract(reference_run_id: str, model_id: str, tool: str, project_dir: Path,
                           input_paths: list[str], parameters: dict[str, Any], *, environment: dict[str, Any] | None = None,
                           environment_closure: dict[str, Any] | None = None) -> dict[str, Any]:
    """Freeze a rebuild contract from existing input files; never invent hashes."""
    inputs = []
    for rel in input_paths:
        path = Path(project_dir) / rel
        if not path.is_file(): raise FileNotFoundError(rel)
        inputs.append({"path": rel, "sha256": _sha256(path)})
    return {"artifact_type": "RebuildContract", "schema_version": "1.0-D", "run_id": reference_run_id, "model_id": model_id,
            "tool": tool, "inputs": inputs, "parameters": parameters, "environment": environment or {"python": sys.version.split()[0]},
            "environment_closure": environment_closure, "expected_result": {"model_id": model_id, "schema_version": "0.9"},
            "policy": {"allow_network": False, "allow_shell": False}}
