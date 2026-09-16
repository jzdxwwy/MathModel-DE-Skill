from tools.verification.evidence_lineage import build_lineage
from tools.verification.recompute_engine import recompute


def test_shortest_path_recompute():
    result = {
        "model_id": "shortest_path",
        "outputs": [
            {"name": "path", "value": ["A", "B", "C"], "unit": ""},
            {"name": "path_edges", "value": [{"u": "A", "v": "B", "weight": 2}, {"u": "B", "v": "C", "weight": 3}], "unit": ""},
            {"name": "distance", "value": 5, "unit": "km"},
        ],
        "metrics": {},
    }
    assert recompute("shortest_path", result)[0]["status"] == "PASS"


def test_monte_carlo_mean_recompute():
    samples = [1, 2, 3, 4]
    result = {"model_id": "monte_carlo", "outputs": [{"name": "samples", "value": samples, "unit": ""}], "metrics": {"mean": 2.5}}
    assert recompute("monte_carlo", result)[0]["status"] == "PASS"


def test_lineage_contains_result_and_verification():
    manifest = {"run_id": "run-test", "model": "linear_regression", "input_refs": ["data/profile.json"]}
    result = {"run_id": "run-test", "model_id": "linear_regression", "provenance": {"input_refs": ["data/profile.json"]}}
    report = {"gate_decision": "PASS"}
    lineage = build_lineage(manifest, result, report)
    ids = {n["id"] for n in lineage["nodes"]}
    assert "run:run-test" in ids and "result:run-test" in ids and "verification:run-test" in ids
