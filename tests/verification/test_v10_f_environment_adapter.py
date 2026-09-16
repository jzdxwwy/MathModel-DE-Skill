from tools.runtime.environment_adapter import DeclarativeEnvironmentAdapter, capture_runtime_environment, verify_clean_room_evidence


def test_adapter_fingerprint_is_stable():
    a = DeclarativeEnvironmentAdapter(adapter_id="test", kind="VENV", definition={"python": "3.12"})
    assert a.describe()["fingerprint"] == a.describe()["fingerprint"]


def test_runtime_environment_contains_required_closure_fields():
    env = capture_runtime_environment(packages=[{"name": "numpy", "version": "1.0"}], inputs=[{"path": "x.csv", "sha256": "a"}])
    for key in ("python", "platform", "packages", "tools", "source_files", "inputs", "model_refs", "spec_refs", "policy", "fingerprint"):
        assert key in env


def test_clean_room_evidence_detects_python_mismatch():
    ref = capture_runtime_environment()
    observed = dict(ref)
    observed["python"] = {"implementation": "Other", "version": "0"}
    assert verify_clean_room_evidence(ref, observed)["decision"] == "FAIL"


def test_clean_room_evidence_passes_identical_closure():
    ref = capture_runtime_environment()
    observed = dict(ref)
    assert verify_clean_room_evidence(ref, observed)["decision"] == "PASS"
