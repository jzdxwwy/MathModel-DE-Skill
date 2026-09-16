"""V1.0-I concrete Python venv materialization.

This adapter creates a fresh Python virtual environment only. It deliberately
has no package-install or arbitrary-command interface: dependency installation
and model execution remain separate trusted-host responsibilities.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
import uuid
import venv
from pathlib import Path
from typing import Any


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def materialize_venv(contract: dict[str, Any], *, output_dir: str | Path) -> dict[str, Any]:
    """Create a brand-new venv and return host-observed materialization evidence.

    The target is always created below ``output_dir`` and must not pre-exist.
    No shell, pip, network, or model-generated command is invoked here.
    """
    if contract.get("artifact_type") != "VenvMaterializationContract":
        raise ValueError("invalid VenvMaterializationContract artifact_type")
    if contract.get("schema_version") != "1.0-I":
        raise ValueError("unsupported VenvMaterializationContract schema_version")
    if contract.get("fresh") is not True:
        raise ValueError("V1.0-I requires fresh=true")
    policy = contract.get("policy", {})
    if policy != {"allow_network": False, "allow_shell": False, "isolation_required": True}:
        raise PermissionError("V1.0-I venv materialization requires network=false, shell=false, isolation_required=true")

    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / str(contract["target_dir"])).resolve()
    if target == root or root not in target.parents:
        raise ValueError("target_dir must be a child of output_dir")
    if target.exists():
        raise FileExistsError(f"fresh materialization target already exists: {target}")

    builder = venv.EnvBuilder(with_pip=False, clear=False, symlinks=False)
    builder.create(str(target))
    py_name = "python.exe" if platform.system().lower().startswith("win") else "python"
    interpreter = target / ("Scripts" if platform.system().lower().startswith("win") else "bin") / py_name
    if not interpreter.is_file():
        raise RuntimeError("venv created but interpreter was not materialized")

    evidence = {
        "artifact_type": "VenvMaterializationEvidence",
        "schema_version": "1.0-I",
        "materialization_id": str(contract["materialization_id"]),
        "adapter_id": str(contract["adapter_id"]),
        "status": "MATERIALIZED",
        "fresh": True,
        "target_dir": str(target),
        "interpreter": str(interpreter),
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "host": {
            "os": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "policy": dict(policy),
        "lock_hash": str(contract["lock_hash"]),
        "interpreter_sha256": _sha256_bytes(interpreter.read_bytes()),
    }
    body = dict(evidence)
    evidence["fingerprint"] = _sha256_bytes(_canonical(body).encode("utf-8"))
    return evidence
