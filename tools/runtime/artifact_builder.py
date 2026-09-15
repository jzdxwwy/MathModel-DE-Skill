"""V0.7-B structured Artifact generation and gate helpers.

The LLM proposes semantic content; deterministic ingestion facts remain
authoritative. This module normalizes, validates, and persists the three
front-end artifacts required by Stages 00-02.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    Draft202012Validator = None  # type: ignore


SCHEMAS = {
    "ProblemSpec": "problem-spec.schema.json",
    "ProblemMap": "problem-map.schema.json",
    "DataProfile": "data-profile.schema.json",
}


def _schema(repo_root: Path, artifact_type: str) -> dict[str, Any]:
    path = repo_root / "artifacts" / "schemas" / SCHEMAS[artifact_type]
    return json.loads(path.read_text(encoding="utf-8"))


def validate_artifact(repo_root: Path, artifact: dict[str, Any], artifact_type: str) -> list[str]:
    if Draft202012Validator is None:
        return ["jsonschema dependency is not installed"]
    validator = Draft202012Validator(_schema(repo_root, artifact_type))
    errors = sorted(validator.iter_errors(artifact), key=lambda e: list(e.path))
    return [f"{'.'.join(str(x) for x in e.path) or '<root>'}: {e.message}" for e in errors]


def _unwrap(output: dict[str, Any], artifact_type: str) -> dict[str, Any]:
    """Accept direct artifact JSON or the documented envelope."""
    candidate = output.get("artifact") if isinstance(output.get("artifact"), dict) else output
    if candidate.get("artifact_type") == artifact_type:
        return dict(candidate)
    return dict(candidate)


def _base_status(artifact: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    artifact["status"] = "VALIDATED" if not errors else "DRAFT"
    return artifact


def build_problem_spec(repo_root: Path, output: dict[str, Any], problem_input: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    artifact = _unwrap(output, "ProblemSpec")
    artifact.setdefault("artifact_type", "ProblemSpec")
    artifact.setdefault("schema_version", "0.1")
    artifact.setdefault("status", "DRAFT")
    problem_id = artifact.get("problem_id") or problem_input.get("problem_id") or "problem-001"
    artifact["problem_id"] = problem_id
    source = artifact.setdefault("source", {})
    source.setdefault("title", problem_input.get("problem", "")[:120] or "Untitled problem")
    source.setdefault("mode", "problem_solving")
    artifact.setdefault("data_assets", [a.get("name", a.get("path", "")) for a in problem_input.get("attachments", [])])
    errors = validate_artifact(repo_root, artifact, "ProblemSpec")
    return _base_status(artifact, errors), errors


def build_problem_map(repo_root: Path, output: dict[str, Any], problem_spec: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    artifact = _unwrap(output, "ProblemMap")
    artifact.setdefault("artifact_type", "ProblemMap")
    artifact.setdefault("schema_version", "0.1")
    artifact.setdefault("status", "DRAFT")
    artifact.setdefault("problem_id", problem_spec["problem_id"])
    artifact.setdefault("problem_type", problem_spec.get("problem_type", []))
    spec_ids = {t["task_id"] for t in problem_spec.get("tasks", [])}
    tasks = artifact.get("tasks", [])
    map_ids = {t.get("task_id") for t in tasks}
    if spec_ids and map_ids != spec_ids:
        artifact["open_questions"] = list(artifact.get("open_questions", [])) + [
            f"ProblemMap task IDs {sorted(map_ids)} do not exactly match ProblemSpec task IDs {sorted(spec_ids)}"
        ]
    errors = validate_artifact(repo_root, artifact, "ProblemMap")
    if spec_ids and map_ids != spec_ids:
        errors.append("cross-artifact task_id mismatch")
    return _base_status(artifact, errors), errors


def merge_data_profile(deterministic: dict[str, Any], proposed: dict[str, Any]) -> dict[str, Any]:
    """Merge semantic LLM additions without allowing it to rewrite source facts."""
    merged = dict(deterministic)
    proposed = _unwrap(proposed, "DataProfile")
    merged["artifact_type"] = "DataProfile"
    merged["schema_version"] = deterministic.get("schema_version", "0.1")
    merged["status"] = "DRAFT"
    merged["assets"] = deterministic.get("assets", [])
    existing_risks = list(deterministic.get("data_risks", []))
    proposed_risks = [str(x) for x in proposed.get("data_risks", [])]
    merged["data_risks"] = list(dict.fromkeys(existing_risks + proposed_risks))
    if proposed.get("gate_decision") == "FAIL" or deterministic.get("gate_decision") == "FAIL":
        merged["gate_decision"] = "FAIL"
    elif merged["data_risks"]:
        merged["gate_decision"] = "PASS_WITH_WARNINGS"
    else:
        merged["gate_decision"] = deterministic.get("gate_decision", "PASS")
    return merged


def build_data_profile(repo_root: Path, deterministic: dict[str, Any], output: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    artifact = merge_data_profile(deterministic, output)
    errors = validate_artifact(repo_root, artifact, "DataProfile")
    return _base_status(artifact, errors), errors


def persist_artifact(project_dir: Path, name: str, artifact: dict[str, Any]) -> Path:
    path = project_dir / "artifacts" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
