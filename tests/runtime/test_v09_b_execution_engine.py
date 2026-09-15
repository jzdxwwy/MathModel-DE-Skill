import json
from pathlib import Path

from tools.runtime.execution_engine import ToolExecutionEngine
from tools.runtime.tool_registry import ToolRegistry
from tools.runtime.v09_tools import register_default_tools

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "v09_b_regression.csv"


def test_execution_engine_writes_schema_shape(tmp_path):
    registry = ToolRegistry()
    register_default_tools(registry)
    engine = ToolExecutionEngine(ROOT, registry)
    dispatch = {
        "dispatches": [{
            "task_id": "Q1",
            "model_id": "linear_regression",
            "tool": "python.baseline_regression",
            "inputs": ["DataProfile", "ProblemMap"],
            "outputs": ["RunManifest", "ResultBundle"],
            "status": "READY",
            "binding": {"data_path": str(FIXTURE), "target": "target", "features": ["x1", "x2"]},
        }]
    }
    manifests = engine.execute(dispatch, tmp_path, "fixture problem")
    assert manifests[0]["status"] == "RUN_COMPLETE"
    bundle = list((tmp_path / "runs").glob("*/result-bundle.json"))[0]
    payload = json.loads(bundle.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "ResultBundle"
    assert "outputs" in payload and "provenance" in payload
    assert "results" not in payload


def test_execution_engine_fails_closed_without_binding(tmp_path):
    registry = ToolRegistry()
    register_default_tools(registry)
    engine = ToolExecutionEngine(ROOT, registry)
    dispatch = {
        "dispatches": [{
            "task_id": "Q1",
            "model_id": "linear_regression",
            "tool": "python.baseline_regression",
            "inputs": ["DataProfile", "ProblemMap"],
            "outputs": ["RunManifest", "ResultBundle"],
            "status": "PLANNED",
        }]
    }
    manifests = engine.execute(dispatch, tmp_path, "fixture problem")
    assert manifests[0]["status"] == "INPUT_BLOCKED"
