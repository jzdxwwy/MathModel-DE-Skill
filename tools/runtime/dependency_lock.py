"""V1.0-G deterministic dependency-lock construction and verification.

This module is declarative: it never invokes pip/conda/docker/shell. A trusted
host may materialize the lock later through an approved adapter.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def fingerprint(value: dict[str, Any]) -> str:
    body = dict(value)
    body.pop("fingerprint", None)
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()


def build_dependency_lock(*, lock_id: str, adapter_id: str, python: dict[str, str],
                           packages: list[dict[str, Any]] | None = None,
                           tools: list[dict[str, Any]] | None = None,
                           base_image: str | None = None,
                           source_files: list[dict[str, str]] | None = None) -> dict[str, Any]:
    lock: dict[str, Any] = {
        "artifact_type": "DependencyLockManifest",
        "schema_version": "1.0-G",
        "lock_id": lock_id,
        "adapter_id": adapter_id,
        "python": python,
        "packages": sorted(packages or [], key=lambda x: (str(x.get("name", "")), str(x.get("version", "")))),
        "tools": sorted(tools or [], key=lambda x: (str(x.get("name", "")), str(x.get("version", "")))),
        "source_files": sorted(source_files or [], key=lambda x: str(x.get("path", ""))),
    }
    if base_image:
        lock["base_image"] = base_image
    lock["fingerprint"] = fingerprint(lock)
    return lock


def verify_lock_hash(lock: dict[str, Any], expected: str) -> bool:
    return bool(lock) and lock.get("fingerprint") == expected and fingerprint(lock) == expected


def verify_source_hashes(lock: dict[str, Any], project_dir: str | Path) -> list[str]:
    root = Path(project_dir)
    mismatches: list[str] = []
    for item in lock.get("source_files", []):
        path = root / str(item.get("path", ""))
        expected = str(item.get("sha256", ""))
        if not path.is_file():
            mismatches.append(str(path))
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            mismatches.append(str(path))
    return mismatches
