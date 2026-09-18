"""V1.0-K host-owned fixed module entrypoint."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from .tool_registry import ToolRegistry
from .v09_tools import register_default_tools
def main(argv=None)->int:
 p=argparse.ArgumentParser(); p.add_argument("--tool",required=True); p.add_argument("--payload",required=True); p.add_argument("--output",required=True); a=p.parse_args(argv)
 root=Path(a.output).resolve(); payload=json.loads(Path(a.payload).read_text(encoding="utf-8"))
 r=ToolRegistry(); register_default_tools(r); r.get(a.tool); result=r.invoke(a.tool,**payload)
 if isinstance(result,dict) and result.get("artifact_type")=="ResultBundle": bundle=result
 else: bundle={"artifact_type":"ResultBundle","schema_version":"1.0-K","status":"VALIDATED","run_id":payload.get("run_id"),"model_id":payload.get("model_id",a.tool),"outputs":result.get("outputs",[]) if isinstance(result,dict) else [{"name":"result","value":result,"unit":"value"}],"metrics":result.get("metrics",{}) if isinstance(result,dict) else {},"artifacts":result.get("artifacts",[]) if isinstance(result,dict) else [],"warnings":[],"provenance":{"code_ref":a.tool,"environment":"venv"}}
 (root/"result-bundle.json").write_text(json.dumps(bundle,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8"); return 0
if __name__=="__main__": raise SystemExit(main())
