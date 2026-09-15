"""Static contract checks for V0.6 runtime components.

These tests are intentionally lightweight. They are committed as executable
checks, but this environment does not provide a repository shell runner, so
passing execution is not claimed here.
"""
from pathlib import Path

from tools.runtime.model_adapter import ModelRequest, ModelResponse
from tools.runtime.task_context import TaskContext
from tools.runtime.tool_registry import ToolRegistry, ToolSpec


ROOT = Path(__file__).resolve().parents[2]


def test_runtime_files_exist():
    for name in [
        "model_adapter.py",
        "skill_loader.py",
        "task_context.py",
        "tool_registry.py",
        "orchestrator.py",
        "execution_protocol.md",
    ]:
        assert (ROOT / "tools" / "runtime" / name).exists()


def test_model_contract():
    request = ModelRequest(task_id="t1", stage="00-start", instruction="x")
    response = ModelResponse(status="ok", output={"x": 1})
    assert request.task_id == "t1"
    assert response.status == "ok"


def test_tool_registry():
    registry = ToolRegistry([
        ToolSpec("echo", "test", lambda value: value, ["value"], ["value"])
    ])
    assert registry.invoke("echo", value=3) == 3
    assert registry.describe()[0]["name"] == "echo"


def test_context_persistence_shape(tmp_path):
    ctx = TaskContext(task_id="t1", project_dir=tmp_path)
    ctx.set_stage("00-start", "PASS")
    path = ctx.persist()
    assert path.exists()
    assert "00-start" in path.read_text(encoding="utf-8")
