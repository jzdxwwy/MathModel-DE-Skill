"""V1.0-M canonical ResultBundle builder.

All execution entrypoints should use this builder instead of defining a
parallel ResultBundle schema.
"""
from __future__ import annotations
from typing import Any

def build_result_bundle(*, run_id:str|None, model_id:str, tool_ref:str,
                        result:Any, schema_version:str="1.0-M")->dict[str,Any]:
    if isinstance(result,dict) and result.get("artifact_type")=="ResultBundle":
        bundle=dict(result)
        bundle.setdefault("schema_version",schema_version)
        return bundle
    if isinstance(result,dict):
        outputs=result.get("outputs",[])
        metrics=result.get("metrics",{})
        artifacts=result.get("artifacts",[])
    else:
        outputs=[{"name":"result","value":result,"unit":"value"}]
        metrics={}; artifacts=[]
    return {
        "artifact_type":"ResultBundle","schema_version":schema_version,
        "status":"VALIDATED","run_id":run_id,"model_id":model_id,
        "outputs":outputs,"metrics":metrics,"artifacts":artifacts,
        "warnings":[],"provenance":{"code_ref":tool_ref,"environment":"target-venv"}
    }
