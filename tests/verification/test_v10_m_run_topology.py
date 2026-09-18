import json
from pathlib import Path
from tools.runtime.run_layout import resolve_run_layout
from tools.verification.unified_reproducibility_gate import evaluate_unified_reproducibility_gate

def _evidence(run_id, tool="demo", lock="L", env="E", inputs=None):
    return {
        "artifact_type":"UnifiedExecutionEvidence","schema_version":"1.0-M",
        "execution_id":run_id,"run_id":run_id,"execution_status":"SUCCESS",
        "adapter_id":"test","isolation_id":"iso-"+run_id,"tool_ref":tool,
        "interpreter":"python","input_hashes":inputs or [{"path":"x","sha256":"a"*64}],
        "lock_hash":lock,"environment_fingerprint":env,
        "execution_log_hash":"b"*64,"result_bundle_hash":"c"*64,
        "source_evidence":["venv-tool-execution-evidence.json"],
        "observed_at":"2026-01-01T00:00:00+00:00","canonical_fingerprint":"d"*64
    }

def _bundle(run_id, value=1):
    return {
        "artifact_type":"ResultBundle","schema_version":"1.0-M","status":"VALIDATED",
        "run_id":run_id,"model_id":"demo",
        "outputs":[{"name":"value","value":value,"unit":"u"}],"metrics":{},
        "artifacts":[],"warnings":[],"provenance":{"code_ref":"demo"}
    }

def test_run_layout_paths(tmp_path):
    layout=resolve_run_layout(tmp_path/"run-1")
    assert layout.execution == (tmp_path/"run-1"/"reference"/"execution")
    assert layout.result_bundle.name=="result-bundle.json"
    assert layout.execution_log.name=="execution.log"
    assert layout.unified_execution_evidence.name=="unified-execution-evidence.json"

def test_unified_reproducibility_pass(tmp_path):
    ref=tmp_path/"ref"; reb=tmp_path/"reb"
    for d in (ref,reb):
        d.mkdir()
        (d/"unified-execution-evidence.json").write_text(json.dumps(_evidence(d.name)),encoding="utf-8")
    (ref/"result-bundle.json").write_text(json.dumps(_bundle("ref")),encoding="utf-8")
    (reb/"result-bundle.json").write_text(json.dumps(_bundle("reb")),encoding="utf-8")
    r=evaluate_unified_reproducibility_gate(ref,reb)
    assert r["gate_decision"]=="PASS"

def test_unified_reproducibility_identity_fail(tmp_path):
    ref=tmp_path/"ref"; reb=tmp_path/"reb"
    for d in (ref,reb):
        d.mkdir()
    (ref/"unified-execution-evidence.json").write_text(json.dumps(_evidence("ref",env="E1")),encoding="utf-8")
    (reb/"unified-execution-evidence.json").write_text(json.dumps(_evidence("reb",env="E2")),encoding="utf-8")
    (ref/"result-bundle.json").write_text(json.dumps(_bundle("ref")),encoding="utf-8")
    (reb/"result-bundle.json").write_text(json.dumps(_bundle("reb")),encoding="utf-8")
    r=evaluate_unified_reproducibility_gate(ref,reb)
    assert r["gate_decision"]=="FAIL"
    assert "environment_fingerprint" in r["identity_mismatches"]
