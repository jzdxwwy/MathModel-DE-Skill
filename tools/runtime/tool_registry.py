"""Provider-neutral registry describing executable tools available to the runtime."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Optional


@dataclass
class ToolSpec:
    name: str
    purpose: str
    handler: Callable[..., Any]
    input_names: list[str] = field(default_factory=list)
    output_names: list[str] = field(default_factory=list)


class ToolRegistry:
    def __init__(self, tools: Optional[Iterable[ToolSpec]] = None):
        self._tools: Dict[str, ToolSpec] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: ToolSpec) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolSpec:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def describe(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "purpose": t.purpose,
                "inputs": t.input_names,
                "outputs": t.output_names,
            }
            for t in self._tools.values()
        ]

    def invoke(self, name: str, **kwargs: Any) -> Any:
        return self.get(name).handler(**kwargs)
