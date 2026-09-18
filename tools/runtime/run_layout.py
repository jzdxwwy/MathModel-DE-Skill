"""V1.0-M canonical run topology.

This module only resolves paths; it does not execute code or move artifacts.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass(frozen=True)
class RunLayout:
    root: Path
    run_id: str

    @property
    def reference(self)->Path: return self.root/"reference"
    @property
    def execution(self)->Path: return self.reference/"execution"
    @property
    def verification(self)->Path: return self.reference/"verification"
    @property
    def result_bundle(self)->Path: return self.execution/"result-bundle.json"
    @property
    def execution_log(self)->Path: return self.execution/"execution.log"
    @property
    def unified_execution_evidence(self)->Path: return self.execution/"unified-execution-evidence.json"

    def rebuild(self, rebuild_id:str)->Path: return self.root/"rebuild"/rebuild_id
    def replay(self, replay_id:str)->Path: return self.root/"replay"/replay_id

    def topology(self)->dict:
        return {
            "artifact_type":"RunTopology","schema_version":"1.0-M","run_id":self.run_id,
            "reference_dir":"reference",
            "rebuild_dirs":[],"replay_dirs":[],
            "canonical_artifacts":{
                "result_bundle":"execution/result-bundle.json",
                "execution_log":"execution/execution.log",
                "unified_execution_evidence":"execution/unified-execution-evidence.json"
            }
        }

    def write(self)->Path:
        self.root.mkdir(parents=True,exist_ok=True)
        p=self.root/"run-topology.json"
        p.write_text(json.dumps(self.topology(),ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
        return p

def resolve_run_layout(run_dir:str|Path)->RunLayout:
    root=Path(run_dir).resolve()
    return RunLayout(root=root,run_id=root.name)
