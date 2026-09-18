"""V1.0-L closes K execution evidence into the existing V1.0-C comparison."""
from __future__ import annotations
import json
from pathlib import Path
from .reproducibility_gate import compare_result_bundles
def evaluate_reproducibility_closure(reference_dir:str|Path,rebuild_dir:str|Path)->dict:
 ref=Path(reference_dir); reb=Path(rebuild_dir)
 try:r=json.loads((ref/"result-bundle.json").read_text(encoding="utf-8")); b=json.loads((reb/"result-bundle.json").read_text(encoding="utf-8"))
 except Exception as exc:return {"artifact_type":"ReproducibilityClosureReport","schema_version":"1.0-L","gate_decision":"NOT_RUN","reason":str(exc)}
 mismatches=compare_result_bundles(r,b)
 return {"artifact_type":"ReproducibilityClosureReport","schema_version":"1.0-L","gate_decision":"FAIL" if mismatches else "PASS","reference_run_id":ref.name,"rebuild_run_id":reb.name,"mismatches":mismatches,"comparison":{"atol":1e-8,"rtol":1e-6}}
