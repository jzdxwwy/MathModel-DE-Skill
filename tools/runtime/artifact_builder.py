"""V0.7-B/V0.8 structured Artifact generation and gate helpers."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None  # type: ignore

SCHEMAS={"ProblemSpec":"problem-spec.schema.json","ProblemMap":"problem-map.schema.json","DataProfile":"data-profile.schema.json","ModelPlan":"model-plan.schema.json","ModelSpec":"model-spec.schema.json","ModelComparison":"model-comparison.schema.json","ToolDispatchPlan":"tool-dispatch.schema.json"}

def _schema(repo_root: Path, artifact_type: str)->dict[str,Any]:
    return json.loads((repo_root/"artifacts"/"schemas"/SCHEMAS[artifact_type]).read_text(encoding="utf-8"))

def validate_artifact(repo_root: Path, artifact: dict[str,Any], artifact_type: str)->list[str]:
    if Draft202012Validator is None: return ["jsonschema dependency is not installed"]
    validator=Draft202012Validator(_schema(repo_root,artifact_type))
    errors=sorted(validator.iter_errors(artifact),key=lambda e:list(e.path))
    return [f"{'.'.join(str(x) for x in e.path) or '<root>'}: {e.message}" for e in errors]

def _unwrap(output: dict[str,Any])->dict[str,Any]:
    candidate=output.get("artifact") if isinstance(output.get("artifact"),dict) else output
    return dict(candidate)

def _base_status(artifact:dict[str,Any],errors:list[str])->dict[str,Any]:
    artifact["status"]="VALIDATED" if not errors else "DRAFT"
    return artifact

def build_problem_spec(repo_root,output,problem_input):
    artifact=_unwrap(output); artifact.setdefault("artifact_type","ProblemSpec"); artifact.setdefault("schema_version","0.1"); artifact.setdefault("status","DRAFT")
    artifact["problem_id"]=artifact.get("problem_id") or problem_input.get("problem_id") or "problem-001"
    source=artifact.setdefault("source",{}); source.setdefault("title",problem_input.get("problem","")[:120] or "Untitled problem"); source.setdefault("mode","problem_solving")
    artifact.setdefault("data_assets",[a.get("name",a.get("path","")) for a in problem_input.get("attachments",[])])
    errors=validate_artifact(repo_root,artifact,"ProblemSpec"); return _base_status(artifact,errors),errors

def build_problem_map(repo_root,output,problem_spec):
    artifact=_unwrap(output); artifact.setdefault("artifact_type","ProblemMap"); artifact.setdefault("schema_version","0.1"); artifact.setdefault("status","DRAFT"); artifact.setdefault("problem_id",problem_spec["problem_id"]); artifact.setdefault("problem_type",problem_spec.get("problem_type",[]))
    spec_ids={t["task_id"] for t in problem_spec.get("tasks",[])}; map_ids={t.get("task_id") for t in artifact.get("tasks",[])}
    errors=validate_artifact(repo_root,artifact,"ProblemMap")
    if spec_ids and map_ids!=spec_ids: errors.append(f"cross-artifact task_id mismatch: spec={sorted(spec_ids)}, map={sorted(map_ids)}")
    return _base_status(artifact,errors),errors

def merge_data_profile(deterministic,proposed):
    merged=dict(deterministic); proposed=_unwrap(proposed); merged["artifact_type"]="DataProfile"; merged["schema_version"]=deterministic.get("schema_version","0.1"); merged["status"]="DRAFT"; merged["assets"]=deterministic.get("assets",[])
    merged["data_risks"]=list(dict.fromkeys(list(deterministic.get("data_risks",[]))+[str(x) for x in proposed.get("data_risks",[])]))
    if proposed.get("gate_decision")=="FAIL" or deterministic.get("gate_decision")=="FAIL": merged["gate_decision"]="FAIL"
    elif merged["data_risks"]: merged["gate_decision"]="PASS_WITH_WARNINGS"
    else: merged["gate_decision"]=deterministic.get("gate_decision","PASS")
    return merged

def build_data_profile(repo_root,deterministic,output):
    artifact=merge_data_profile(deterministic,output); errors=validate_artifact(repo_root,artifact,"DataProfile"); return _base_status(artifact,errors),errors

def persist_artifact(project_dir:Path,name:str,artifact:dict[str,Any])->Path:
    path=project_dir/"artifacts"/f"{name}.json"; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(artifact,ensure_ascii=False,indent=2),encoding="utf-8"); return path
