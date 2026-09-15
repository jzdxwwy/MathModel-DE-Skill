"""Model adapter protocol.

The runtime owns orchestration; an LLM adapter owns model interaction.
A concrete adapter can wrap Claude Code, Codex, an API client, or a local model.
The V0.6 protocol deliberately avoids provider-specific SDKs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol


@dataclass
class ModelRequest:
    task_id: str
    stage: str
    instruction: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    status: str
    output: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    raw: Optional[Any] = None


class ModelAdapter(Protocol):
    """Provider-neutral contract used by the runtime."""

    def invoke(self, request: ModelRequest) -> ModelResponse:
        ...


class CallbackModelAdapter:
    """Small adapter for embedding the runtime in an existing host application."""

    def __init__(self, callback):
        self.callback = callback

    def invoke(self, request: ModelRequest) -> ModelResponse:
        result = self.callback(request)
        if isinstance(result, ModelResponse):
            return result
        if isinstance(result, dict):
            return ModelResponse(status="ok", output=result)
        return ModelResponse(status="ok", message=str(result))
