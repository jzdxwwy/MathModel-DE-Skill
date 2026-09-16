"""V1.0-G trusted environment-adapter registry.

Only explicitly registered and trusted adapters may be selected. The registry
contains metadata and factories; it does not execute shell commands itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class RegisteredAdapter:
    adapter_id: str
    kind: str
    trusted: bool
    capabilities: dict[str, bool]
    factory: Callable[..., Any] | None = None


class AdapterRegistry:
    def __init__(self) -> None:
        self._items: dict[str, RegisteredAdapter] = {}

    def register(self, adapter: RegisteredAdapter) -> None:
        if adapter.adapter_id in self._items:
            raise ValueError(f"adapter already registered: {adapter.adapter_id}")
        self._items[adapter.adapter_id] = adapter

    def get(self, adapter_id: str) -> RegisteredAdapter | None:
        return self._items.get(adapter_id)

    def require_trusted(self, adapter_id: str) -> RegisteredAdapter:
        item = self.get(adapter_id)
        if item is None:
            raise KeyError(f"unknown environment adapter: {adapter_id}")
        if not item.trusted:
            raise PermissionError(f"untrusted environment adapter: {adapter_id}")
        return item

    def describe(self) -> dict[str, Any]:
        return {"adapters": [
            {"adapter_id": x.adapter_id, "kind": x.kind, "trusted": x.trusted,
             "capabilities": x.capabilities}
            for x in self._items.values()
        ]}
