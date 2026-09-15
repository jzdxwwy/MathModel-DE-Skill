"""V0.9 helper for executing a validated dispatch plan from a host output directory."""
from __future__ import annotations
import json
from pathlib import Path
from .execution_engine import ToolExecutionEngine
from .tool_registry import ToolRegistry
from .v09_tools import register_default_tools


def execute_dispatch(project_dir: Path, problem: str):
    dispatch_path = project_dir / "artifacts" / "tool-dispatch.json"
    dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    registry = ToolRegistry()
    register_default_tools(registry)
    engine = ToolExecutionEngine(Path(__file__).resolve().parents[2], registry)
    results = engine.execute(dispatch, project_dir, problem)
    (project_dir / "artifacts" / "v09-execution.json").write_text(json.dumps({"status":"COMPLETED","runs":results},ensure_ascii=False,indent=2),encoding="utf-8")
    return results
