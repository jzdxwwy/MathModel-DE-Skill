"""V1.0-G trusted-host execution boundary.

The core Skill cannot create Docker/Conda/venv environments or run arbitrary
commands. A host integration supplies an approved adapter and returns signed-
by-hash execution evidence. The default implementation is intentionally
blocked so that metadata cannot masquerade as execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .adapter_registry import AdapterRegistry


@dataclass
class TrustedHost:
    registry: AdapterRegistry

    def validate(self, adapter_id: str, *, require_isolation: bool = True) -> dict[str, Any]:
        adapter = self.registry.require_trusted(adapter_id)
        if require_isolation and not adapter.capabilities.get("isolation", False):
            raise PermissionError(f"adapter does not provide isolation: {adapter_id}")
        if adapter.capabilities.get("shell", False):
            raise PermissionError("shell-enabled adapters are not permitted by the core policy")
        if adapter.capabilities.get("network", False):
            raise PermissionError("network-enabled adapters are not permitted by the core policy")
        return {"adapter_id": adapter.adapter_id, "kind": adapter.kind,
                "capabilities": dict(adapter.capabilities), "trusted": adapter.trusted}

    def execute(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("TrustedHost.execute requires an external approved host integration")
