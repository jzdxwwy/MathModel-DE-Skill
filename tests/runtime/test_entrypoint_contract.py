"""Contract tests for the V0.6-B executable boundary.

These tests are intentionally dependency-light. They validate construction of the
normalized request and the deterministic host response without requiring a model API.
"""
from tools.runtime.host_adapter import HostRequest, normalize_problem_input
from tools.runtime.entrypoint import DemoHostAdapter
from pathlib import Path


def test_normalize_problem_input():
    payload = normalize_problem_input("problem.pdf", ["a.xlsx", "b.csv"])
    assert payload["problem"] == "problem.pdf"
    assert payload["attachments"] == ["a.xlsx", "b.csv"]


def test_demo_host_returns_completed(tmp_path):
    request = HostRequest(
        instruction="Run the workflow.",
        problem_input=normalize_problem_input("problem.pdf", []),
        output_dir=str(tmp_path / "run"),
        task_id="test-runtime-001",
    )
    response = DemoHostAdapter(Path(__file__).resolve().parents[2]).run(request)
    assert response.status == "completed"
    assert response.task_id == "test-runtime-001"
    assert response.manifest is not None
