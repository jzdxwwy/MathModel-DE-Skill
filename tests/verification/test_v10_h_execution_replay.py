from pathlib import Path
import hashlib
import json
import pytest

from tools.runtime.adapter_registry import AdapterRegistry, RegisteredAdapter
from tools.runtime.tool_registry import ToolRegistry, ToolSpec
from tools.runtime.execution_replay import ExecutionReplayEngine
from tools.verification.execution_replay_gate import evaluate_execution_replay_gate


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_replay_registered_tool_and_hashes(tmp_path: Path):
    inp = tmp_path / "input.txt"
    inp.write_text("abc", encoding="utf-8")
    out = tmp_path / "run"
    adapters = AdapterRegistry()
    adapters.register(RegisteredAdapter("local-test", "CUSTOM", True,
                                        {"isolation": True, "shell": False, "network": False}))
    tools = ToolRegistry([ToolSpec("echo_result", "test", lambda value: {"status": "VALIDATED", "value": value})])
    engine = ExecutionReplayEngine(adapters=adapters, tools=tools)
    contract = {
        "artifact_type": "ExecutionReplayContract", "schema_version": "1.0-H",
        "run_id": "run-1", "adapter_id": "local-test", "tool": "echo_result",
        "input_hashes": [{"path": "input.txt", "sha256": sha(inp)}],
        "policy": {"allow_network": False, "allow_shell": False, "isolation_required": True},
        "payload": {"value": 7}
    }
    evidence = engine.replay(contract, project_dir=tmp_path, output_dir=out,
                             lock_hash="a" * 64, environment_fingerprint="b" * 64)
    assert evidence["status"] == "EXECUTED"
    assert evaluate_execution_replay_gate(out)["gate_decision"] == "PASS"


def test_unknown_or_untrusted_adapter_is_blocked(tmp_path: Path):
    adapters = AdapterRegistry()
    tools = ToolRegistry([ToolSpec("t", "test", lambda: {})])
    engine = ExecutionReplayEngine(adapters=adapters, tools=tools)
    contract = {"run_id": "r", "adapter_id": "missing", "tool": "t",
                "input_hashes": [], "policy": {"allow_network": False, "allow_shell": False, "isolation_required": True}}
    with pytest.raises(KeyError):
        engine.replay(contract, project_dir=tmp_path, output_dir=tmp_path / "run")
