"""V1.0-K/M host-owned fixed module entrypoint."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from .tool_registry import ToolRegistry
from .v09_tools import register_default_tools
from .result_bundle_builder import build_result_bundle

def main(argv=None)->int:
    p=argparse.ArgumentParser()
    p.add_argument("--tool",required=True); p.add_argument("--payload",required=True); p.add_argument("--output",required=True)
    a=p.parse_args(argv)
    root=Path(a.output).resolve()
    root.mkdir(parents=True,exist_ok=True)
    payload=json.loads(Path(a.payload).read_text(encoding="utf-8"))
    r=ToolRegistry(); register_default_tools(r); r.get(a.tool)
    result=r.invoke(a.tool,**payload)
    bundle=build_result_bundle(
        run_id=payload.get("run_id"),
        model_id=payload.get("model_id",a.tool),
        tool_ref=a.tool,
        result=result,
    )
    (root/"result-bundle.json").write_text(
        json.dumps(bundle,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
