from pathlib import Path
import json

from tools.runtime.environment_closure import capture_environment, fingerprint_closure, persist_environment_closure
from tools.verification.environment_gate import evaluate_environment_gate


def test_fingerprint_is_deterministic(tmp_path: Path):
    c = capture_environment("r1", root=tmp_path, capture_mode="DECLARED")
    assert c["fingerprint"] == fingerprint_closure(c)


def test_missing_rebuild_closure_is_not_run(tmp_path: Path):
    c = capture_environment("r1", root=tmp_path, capture_mode="DECLARED")
    persist_environment_closure(tmp_path, c)
    report = evaluate_environment_gate(tmp_path)
    assert report["gate_decision"] == "NOT_RUN"


def test_equal_closures_pass(tmp_path: Path):
    ref = tmp_path / "ref"; reb = tmp_path / "reb"
    ref.mkdir(); reb.mkdir()
    c1 = capture_environment("r1", root=tmp_path, capture_mode="DECLARED")
    c2 = dict(c1); c2["run_id"] = "rebuild-r1"; c2["fingerprint"] = fingerprint_closure(c2)
    persist_environment_closure(ref, c1); persist_environment_closure(reb, c2)
    report = evaluate_environment_gate(ref, rebuild_dir=reb)
    assert report["gate_decision"] == "PASS"


def test_environment_mismatch_fails(tmp_path: Path):
    ref = tmp_path / "ref"; reb = tmp_path / "reb"
    ref.mkdir(); reb.mkdir()
    c1 = capture_environment("r1", root=tmp_path, capture_mode="DECLARED")
    c2 = dict(c1); c2["run_id"] = "rebuild-r1"; c2["python"] = dict(c1["python"]); c2["python"]["version"] = "0.0-test"; c2["fingerprint"] = fingerprint_closure(c2)
    persist_environment_closure(ref, c1); persist_environment_closure(reb, c2)
    report = evaluate_environment_gate(ref, rebuild_dir=reb)
    assert report["gate_decision"] == "FAIL"
    assert report["mismatches"]
