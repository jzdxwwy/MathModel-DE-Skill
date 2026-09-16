from pathlib import Path

from tools.runtime.venv_adapter import materialize_venv
from tools.verification.materialization_gate import evaluate_materialization_gate, persist_materialization_evidence


def test_fresh_venv_materialization(tmp_path: Path):
    contract = {
        "artifact_type": "VenvMaterializationContract",
        "schema_version": "1.0-I",
        "materialization_id": "mat-test-001",
        "adapter_id": "python-venv-test",
        "python": {"implementation": "CPython", "version": "test"},
        "target_dir": "venv",
        "fresh": True,
        "policy": {"allow_network": False, "allow_shell": False, "isolation_required": True},
        "lock_hash": "a" * 64,
    }
    evidence = materialize_venv(contract, output_dir=tmp_path)
    run_dir = tmp_path / "evidence"
    persist_materialization_evidence(evidence, run_dir)
    report = evaluate_materialization_gate(run_dir)
    assert evidence["status"] == "MATERIALIZED"
    assert Path(evidence["interpreter"]).is_file()
    assert report["gate_decision"] == "PASS"


def test_existing_target_is_blocked(tmp_path: Path):
    target = tmp_path / "venv"
    target.mkdir()
    contract = {
        "artifact_type": "VenvMaterializationContract",
        "schema_version": "1.0-I",
        "materialization_id": "mat-test-002",
        "adapter_id": "python-venv-test",
        "python": {"implementation": "CPython", "version": "test"},
        "target_dir": "venv",
        "fresh": True,
        "policy": {"allow_network": False, "allow_shell": False, "isolation_required": True},
        "lock_hash": "b" * 64,
    }
    try:
        materialize_venv(contract, output_dir=tmp_path)
    except FileExistsError:
        return
    assert False, "existing target must be rejected"
