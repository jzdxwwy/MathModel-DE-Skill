"""V1.0-E environment closure utilities.

The closure is declarative evidence: it records the environment that a
trusted host observed or explicitly declared. It never claims isolation or
rebuild success merely because metadata exists.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def fingerprint_closure(closure: dict[str, Any]) -> str:
    payload = {k: v for k, v in closure.items() if k != "fingerprint"}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _hash_entries(paths: Iterable[str], root: Path) -> list[dict[str, Any]]:
    out = []
    for rel in paths:
        p = root / rel
        if not p.is_file():
            raise FileNotFoundError(rel)
        out.append({"path": rel, "sha256": sha256_file(p), "size": p.stat().st_size})
    return out


def installed_package_versions(names: Iterable[str] | None = None) -> list[dict[str, str]]:
    if names is None:
        return []
    result = []
    for name in sorted(set(names)):
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            version = "MISSING"
        result.append({"name": name, "version": version})
    return result


def capture_environment(
    run_id: str,
    *,
    root: str | Path,
    input_paths: Iterable[str] = (),
    source_paths: Iterable[str] = (),
    packages: Iterable[str] | None = None,
    tools: Iterable[dict[str, Any]] = (),
    model_refs: Iterable[str] = (),
    spec_refs: Iterable[str] = (),
    capture_mode: str = "HOST_OBSERVED",
    network: bool = False,
    shell: bool = False,
    isolation_required: bool = True,
    complete: bool = True,
) -> dict[str, Any]:
    root = Path(root)
    closure: dict[str, Any] = {
        "artifact_type": "EnvironmentClosure",
        "schema_version": "1.0-E",
        "run_id": run_id,
        "capture_mode": capture_mode,
        "fingerprint": "",
        "python": {"version": platform.python_version(), "implementation": platform.python_implementation()},
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine(), "architecture": platform.architecture()[0]},
        "packages": installed_package_versions(packages),
        "tools": sorted([dict(x) for x in tools], key=lambda x: (str(x.get("name", "")), str(x.get("code_ref", "")))),
        "source_files": _hash_entries(source_paths, root),
        "inputs": _hash_entries(input_paths, root),
        "model_refs": sorted(set(model_refs)),
        "spec_refs": sorted(set(spec_refs)),
        "policy": {"network": bool(network), "shell": bool(shell), "isolation_required": bool(isolation_required)},
        "complete": bool(complete),
    }
    closure["fingerprint"] = fingerprint_closure(closure)
    return closure


def persist_environment_closure(run_dir: str | Path, closure: dict[str, Any]) -> Path:
    path = Path(run_dir) / "environment-closure.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(closure, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path
