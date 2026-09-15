"""Host-side adapter contract for invoking MathModel-DE-Skill from an LLM host.

A host (Claude Code, Codex, an API service, or another agent harness) only needs
to translate its native model call into HostRequest/HostResponse. The Runtime
then owns task creation, Skill loading, stage orchestration and artifact state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Protocol


@dataclass
class HostRequest:
    """Normalized request received from an external model host."""

    instruction: str
    problem_input: Dict[str, Any] = field(default_factory=dict)
    output_dir: str = "runtime_run"
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HostResponse:
    """Normalized response returned to the external host."""

    status: str
    task_id: str
    manifest: Optional[str] = None
    message: str = ""
    artifacts: Dict[str, str] = field(default_factory=dict)


class HostAdapter(Protocol):
    def run(self, request: HostRequest) -> HostResponse:
        ...


def normalize_problem_input(problem: Optional[str], attachments: Optional[list[str]]) -> Dict[str, Any]:
    """Build a provider-neutral input envelope from CLI/host values."""
    return {
        "problem": problem or "",
        "attachments": attachments or [],
    }
