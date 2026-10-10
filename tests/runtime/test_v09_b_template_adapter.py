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


def test_multiclass_classification_runs_through_adapter(tmp_path):
    """sklearn >= 1.7 requires an explicit multi_class strategy for multiclass
    roc_auc; the plain "roc_auc" scorer raised
    ValueError: multi_class must be in ('ovo', 'ovr'). Any target with more than
    two classes — including the five keyword classes a D/E problem asks for —
    crashed the classification template."""
    import random

    rng = random.Random(7)
    source = tmp_path / "keywords.csv"
    lines = ["spend,clicks,bucket"]
    for _ in range(80):
        spend = round(rng.uniform(0.0, 100.0), 2)
        clicks = rng.randint(0, 40)
        bucket = min(int(spend // 20), 4)
        lines.append(f"{spend},{clicks},{bucket}")
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = execute_tabular_template(
        ROOT,
        tmp_path,
        tmp_path / "run",
        "logistic_classification",
        {"data_path": str(source), "target": "bucket", "features": ["spend", "clicks"], "seed": 7},
    )

    assert result.outputs[0]["value"] == "completed"
    assert any("classification_cv" in x["path"] for x in result.artifacts)
