from pathlib import Path

from tools.benchmark.benchmark_runner import run_readiness_check


def test_v41_missing_inputs_are_blocked(tmp_path: Path):
    result = run_readiness_check(
        tmp_path / "run",
        "CUMCM-2024E",
        [{"attachment_id": "historical_attachment_1",
          "path": str(tmp_path / "missing.xlsx"), "required": True}],
    )
    assert result["status"] == "BLOCKED"
    assert result["gate_decision"] == "NOT_RUN"
    assert result["stages"][0]["status"] == "BLOCKED"


def test_v41_present_input_is_ready(tmp_path: Path):
    source = tmp_path / "data.csv"
    source.write_text("x,y\n1,2\n", encoding="utf-8")
    result = run_readiness_check(
        tmp_path / "run",
        "CUMCM-2024E",
        [{"attachment_id": "historical_attachment_1",
          "path": str(source), "required": True}],
    )
    assert result["status"] == "READY"
    assert result["gate_decision"] == "NOT_RUN"
    assert result["stages"][0]["status"] == "READY"
