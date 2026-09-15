from pathlib import Path
import json
import shutil

import pytest

from tools.runtime.template_adapter import InputBlocked, execute_tabular_template


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "v09_b_regression.csv"


def test_regression_template_executes_with_explicit_binding(tmp_path):
    result = execute_tabular_template(
        ROOT,
        tmp_path,
        tmp_path / "run",
        "linear_regression",
        {"data_path": str(FIXTURE), "target": "target", "features": ["x1", "x2"], "seed": 7},
    )
    assert result.outputs[0]["value"] == "completed"
    assert result.artifacts
    assert any("baseline_predictions.csv" in x["path"] for x in result.artifacts)


def test_missing_target_is_blocked(tmp_path):
    with pytest.raises(InputBlocked, match="target is required"):
        execute_tabular_template(
            ROOT,
            tmp_path,
            tmp_path / "run",
            "linear_regression",
            {"data_path": str(FIXTURE), "features": ["x1", "x2"]},
        )
