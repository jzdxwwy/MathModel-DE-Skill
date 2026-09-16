"""V1.0-F environment adapter boundary.

Adapters describe and verify execution environments. This module deliberately
contains no arbitrary shell execution and no package-manager side effects.
Actual isolated execution is delegated to a trusted host implementation.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _fingerprint(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


class EnvironmentAdapter(Protocol):
    adapter_id: str
    kind: str

    def describe(self) -> dict[str, Any]: ...
    def verify(self, expected: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class DeclarativeEnvironmentAdapter:
    """Safe adapter for declared/observed environments.

    It does not create an environment. A trusted Host may subclass or wrap it
    to perform actual isolated execution and then return observed evidence.
    """

    adapter_id: str
    kind: str = "HOST"
    policy: dict[str, bool] = field(default_factory=lambda: {
        "allow_network": False, "allow_shell": False, "isolation_required": False
    })
    definition: dict[str, Any] = field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        payload = {
            "artifact_type": "EnvironmentAdapterContract",
            "schema_version": "1.0-F",
            "adapter_id": self.adapter_id,
            "kind": self.kind,
            "policy": self.policy,
            "definition": self.definition,
        }
        payload["fingerprint"] = _fingerprint(payload)
        return payload

    def verify(self, expected: dict[str, Any]) -> dict[str, Any]:
        actual = self.describe()
        expected_fp = expected.get("expected_fingerprint")
        actual_fp = actual.get("fingerprint")
        if expected_fp and expected_fp != actual_fp:
            return {"decision": FAIL, "expected": expected_fp, "actual": actual_fp}
        return {"decision": PASS, "expected": expected_fp, "actual": actual_fp}


def capture_runtime_environment(*, packages: list[dict[str, Any]] | None = None,
                                 tools: list[dict[str, Any]] | None = None,
                                 source_files: list[dict[str, Any]] | None = None,
                                 inputs: list[dict[str, Any]] | None = None,
                                 model_refs: list[str] | None = None,
                                 spec_refs: list[str] | None = None,
                                 adapter_id: str = "host-observed") -> dict[str, Any]:
    """Capture deterministic runtime metadata; file hashes must be supplied by caller."""
    closure = {
        "artifact_type": "EnvironmentClosure",
        "schema_version": "1.0-E",
        "capture_mode": "REBUILD_OBSERVED",
        "adapter_id": adapter_id,
        "python": {"implementation": platform.python_implementation(), "version": platform.python_version()},
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "packages": packages or [],
        "tools": tools or [],
        "source_files": source_files or [],
        "inputs": inputs or [],
        "model_refs": model_refs or [],
        "spec_refs": spec_refs or [],
        "policy": {"allow_network": False, "allow_shell": False, "isolation_required": True},
    }
    closure["fingerprint"] = _fingerprint(closure)
    return closure


def verify_clean_room_evidence(reference: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Compare two closures without treating missing execution evidence as success."""
    if not reference or not observed:
        return {"decision": NOT_RUN, "reason": "reference or observed environment closure missing"}
    if reference.get("fingerprint") == observed.get("fingerprint"):
        return {"decision": PASS, "mismatches": []}
    mismatches: list[str] = []
    for key in sorted(set(reference) | set(observed)):
        if key == "fingerprint":
            continue
        if reference.get(key) != observed.get(key):
            mismatches.append(key)
    return {"decision": FAIL, "mismatches": mismatches}
