"""V0.9 compute-stage bridge: dispatch -> execution -> ResultBundle."""
from __future__ import annotations
import json
from pathlib import Path
from .execution_engine import ToolExecutionEngine
from .tool_registry import ToolRegistry
from .v09_tools import register_default_tools


def run_v09(project_dir: Path, problem: str, dispatch_path: Path) -> list[dict]:
    dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    registry = ToolRegistry()
    register_default_tools(registry)
    engine = ToolExecutionEngine(Path(__file__).resolve().parents[2], registry)
    return engine.execute(dispatch, project_dir, problem)
