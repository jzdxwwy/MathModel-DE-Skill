from tools.modeling.data_binding import resolve_binding


def profile():
    return {"assets": [{
        "asset_id": "data1", "path_or_ref": "data/input.csv", "format": "csv",
        "size": {"rows": 100, "columns": 4},
        "schema": [
            {"name": "x1", "dtype": "float", "role": "feature"},
            {"name": "x2", "dtype": "float", "role": "feature"},
            {"name": "y", "dtype": "float", "role": "target"},
            {"name": "date", "dtype": "datetime", "role": "time"},
        ],
        "quality": {"missing": "none", "duplicates": "none", "anomalies": "none"}
    }]}


def test_regression_auto_binds_target_and_features():
    b = resolve_binding("linear_regression", {"task_id": "Q1"}, profile())
    assert b["binding_status"] == "AUTO_BOUND"
    assert b["target"] == "y"
    assert b["features"] == ["x1", "x2"]


def test_time_series_requires_unique_time_role():
    b = resolve_binding("time_series_baseline", {"task_id": "Q2"}, profile())
    assert b["binding_status"] == "AUTO_BOUND"
    assert b["time_col"] == "date"


def test_optimization_blocks_without_explicit_math_binding():
    b = resolve_binding("optimization", {"task_id": "Q3"}, profile())
    assert b["binding_status"] == "BLOCKED"
