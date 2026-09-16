"""V1.0-H controlled execution replay on a trusted Host.

This implementation never executes shell commands. It replays only a tool
already registered in ToolRegistry after validating the replay contract,
input hashes, trusted adapter and lock/environment identities. The resulting
execution evidence is hash-linked to the produced ResultBundle and log.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from .adapter_registry import AdapterRegistry
from .tool_registry import ToolRegistry
from .trusted_host import TrustedHost


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _hash_value(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


class ExecutionReplayEngine:
    def __init__(self, *, adapters: AdapterRegistry, tools: ToolRegistry):
        self.host = TrustedHost(adapters)
        self.tools = tools

    def replay(self, contract: dict[str, Any], *, project_dir: str | Path, output_dir: str | Path,
               lock_hash: str | None = None, environment_fingerprint: str | None = None) -> dict[str, Any]:
        root = Path(project_dir)
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        run_id = str(contract["run_id"])
        isolation_id = "replay-" + uuid.uuid4().hex

        # Fail closed before invoking any tool.
        self.host.validate(contract["adapter_id"], require_isolation=bool(contract["policy"].get("isolation_required", True)))
        self.tools.get(contract["tool"])
        expected_lock = contract.get("expected_lock_hash")
        if expected_lock and lock_hash != expected_lock:
            raise ValueError("dependency lock hash mismatch")
        expected_env = contract.get("expected_environment_fingerprint")
        if expected_env and environment_fingerprint != expected_env:
            raise ValueError("environment fingerprint mismatch")

        for item in contract.get("input_hashes", []):
            path = root / item["path"]
            if not path.is_file() or _sha256(path) != item["sha256"]:
                raise ValueError(f"input hash mismatch: {item['path']}")

        payload = dict(contract.get("payload") or {})
        result = self.tools.invoke(contract["tool"], **payload)
        result_path = out / "result-bundle.json"
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

        log = {
            "run_id": run_id, "isolation_id": isolation_id,
            "adapter_id": contract["adapter_id"], "tool": contract["tool"],
            "input_hashes": contract.get("input_hashes", []),
            "lock_hash": lock_hash, "environment_fingerprint": environment_fingerprint,
            "result_hash": _sha256(result_path),
        }
        log_path = out / "execution-log.json"
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

        evidence = {
            "artifact_type": "ExecutionReplayResult", "schema_version": "1.0-H",
            "run_id": run_id, "status": "EXECUTED", "adapter_id": contract["adapter_id"],
            "tool": contract["tool"], "isolation_id": isolation_id,
            "lock_hash": lock_hash, "environment_fingerprint": environment_fingerprint,
            "input_hashes": contract.get("input_hashes", []),
            "execution_log_sha256": _sha256(log_path),
            "result_bundle_sha256": _sha256(result_path),
        }
        evidence_path = out / "execution-replay-result.json"
        evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return evidence
