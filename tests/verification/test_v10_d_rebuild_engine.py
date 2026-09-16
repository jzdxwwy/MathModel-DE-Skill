from pathlib import Path

from tools.runtime.rebuild_engine import CleanRebuildEngine, build_rebuild_contract, verify_input_hashes
from tools.runtime.tool_registry import ToolRegistry, ToolSpec


def _registry():
    def handler(**kwargs):
        return {"outputs": [{"name": "y", "value": 2.0, "unit": "u"}], "metrics": {"rmse": 0.1}}
    return ToolRegistry([ToolSpec("safe_tool", "test", handler)])


def test_contract_freezes_input_hash(tmp_path: Path):
    (tmp_path / "data.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    c = build_rebuild_contract("run-a", "m1", "safe_tool", tmp_path, ["data.csv"], {})
    assert len(c["inputs"][0]["sha256"]) == 64
    assert verify_input_hashes(c, tmp_path) == []


def test_input_hash_mismatch_blocks_rebuild(tmp_path: Path):
    (tmp_path / "data.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    c = build_rebuild_contract("run-a", "m1", "safe_tool", tmp_path, ["data.csv"], {})
    (tmp_path / "data.csv").write_text("x,y\n1,99\n", encoding="utf-8")
    manifest = CleanRebuildEngine(tmp_path, _registry()).rebuild(c, tmp_path)
    assert manifest["status"] == "BLOCKED"
    assert not (tmp_path / "runs" / manifest["run_id"] / "result-bundle.json").exists()


def test_registered_tool_rebuilds_into_fresh_run(tmp_path: Path):
    (tmp_path / "data.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    c = build_rebuild_contract("run-a", "m1", "safe_tool", tmp_path, ["data.csv"], {})
    manifest = CleanRebuildEngine(tmp_path, _registry()).rebuild(c, tmp_path)
    assert manifest["status"] == "REBUILD_COMPLETE"
    assert (tmp_path / "runs" / manifest["run_id"] / "result-bundle.json").is_file()


def test_unknown_tool_fails_closed(tmp_path: Path):
    (tmp_path / "data.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    c = build_rebuild_contract("run-a", "m1", "missing_tool", tmp_path, ["data.csv"], {})
    manifest = CleanRebuildEngine(tmp_path, _registry()).rebuild(c, tmp_path)
    assert manifest["status"] == "BLOCKED"
    assert manifest["checks"][0]["decision"] == "FAIL"
