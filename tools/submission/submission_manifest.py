"""V0.9-N reproducible SubmissionManifest builder.

The manifest inventories only files that exist and hashes their exact bytes.
It is an audit record, not a claim that the submission is valid; the caller
must supply the upstream gate decisions explicitly.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_submission_manifest(
    project_dir: str | Path,
    run_id: str,
    artifact_paths: Iterable[tuple[str, str | Path]],
    *,
    problem_hash: str | None = None,
    attachment_hashes: list[str] | None = None,
    git_commit: str | None = None,
    environment: dict[str, Any] | None = None,
    paper_manifest_ref: str | None = None,
    presentation_manifest_ref: str | None = None,
    render_manifest_refs: list[str] | None = None,
    verification_report_refs: list[str] | None = None,
    gate_decision: str = "NOT_RUN",
) -> dict[str, Any]:
    root = Path(project_dir)
    artifacts = []
    missing = []
    for kind, raw_path in artifact_paths:
        path = Path(raw_path)
        if not path.is_absolute():
            path = root / path
        if not path.exists() or not path.is_file():
            missing.append(str(path))
            continue
        artifacts.append({
            "kind": str(kind),
            "path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
        })

    decision = "FAIL" if missing else gate_decision
    manifest = {
        "artifact_type": "SubmissionManifest",
        "schema_version": "0.9-N",
        "run_id": str(run_id),
        "problem_hash": problem_hash,
        "attachment_hashes": list(attachment_hashes or []),
        "git_commit": git_commit,
        "environment": dict(environment or {}),
        "artifacts": artifacts,
        "paper_manifest_ref": paper_manifest_ref,
        "presentation_manifest_ref": presentation_manifest_ref,
        "render_manifest_refs": list(render_manifest_refs or []),
        "verification_report_refs": list(verification_report_refs or []),
        "gate_decision": decision,
    }
    if missing:
        manifest["missing_artifacts"] = missing
    return manifest


def persist_submission_manifest(project_dir: str | Path, manifest: dict[str, Any]) -> Path:
    root = Path(project_dir)
    run_id = str(manifest["run_id"])
    path = root / "runs" / run_id / "submission-manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path
