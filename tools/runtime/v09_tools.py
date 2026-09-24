from __future__ import annotations
from pathlib import Path
from typing import Any
from .v09c_contracts import validate_binding

def _tab(**k):
 from .template_adapter import execute_tabular_template
 r=execute_tabular_template(Path(k['repo_root']),Path(k['project_dir']),Path(k['run_dir']),str(k['model_id']),dict(k.get('binding') or {})); return {'execution_mode':'numerical_template','outputs':r.outputs,'metrics':r.metrics,'artifacts':r.artifacts}

def _time(**k):
 from .template_adapter import InputBlocked
 b=dict(k.get('binding') or {}); validate_binding('time_series_baseline',b)
 import pandas as pd, json, os
 p=Path(k['project_dir']).resolve(); src=Path(b['data_path']); src=src if src.is_absolute() else p/src
 if not src.exists(): raise InputBlocked(f'data_path does not exist: {src}')
 run=Path(k['run_dir']); data=run/'data'/'input.csv'; data.parent.mkdir(parents=True,exist_ok=True); df=pd.read_csv(src) if src.suffix.lower()=='.csv' else pd.read_excel(src); miss=[c for c in [b['time_col'],b['target']] if c not in df.columns]
 if miss: raise InputBlocked(f'columns not found: {miss}')
 df.to_csv(data,index=False)
 from .template_adapter import _load_module
 m=_load_module(Path(k['repo_root'])/'05_python/templates/time_series_cv.py'); m.DATA_PATH=data; m.TIME_COL=b['time_col']; m.TARGET=b['target']; m.FEATURES=b.get('features',[]); m.TEST_HORIZON=int(b.get('test_horizon',1)); m.MIN_TRAIN=int(b.get('min_train',10)); m.SEED=int(b.get('seed',20260913)); old=Path.cwd(); os.chdir(run)
 try:m.main()
 finally:os.chdir(old)
 man=run/'results'/'time_series_manifest.json'; notes=json.loads(json.loads(man.read_text())['notes']); return {'execution_mode':'numerical_template','outputs':[{'name':'mean_MAE','value':notes['mean_MAE'],'unit':'error'},{'name':'mean_RMSE','value':notes['mean_RMSE'],'unit':'error'}],'metrics':notes,'artifacts':[{'kind':'csv','path':str(run/'results'/'time_series_cv.csv'),'description':'rolling-origin metrics'}]}

def _graph(**k):
 from .template_adapter import InputBlocked
 b=dict(k.get('binding') or {}); validate_binding('shortest_path',b); import pandas as pd,json,os
 p=Path(k['project_dir']).resolve(); src=Path(b['data_path']); src=src if src.is_absolute() else p/src
 if not src.exists(): raise InputBlocked(f'data_path does not exist: {src}')
 df=pd.read_csv(src)
 if not {'u','v','weight'}.issubset(df.columns): raise InputBlocked('edge CSV must contain u,v,weight')
 run=Path(k['run_dir']); data=run/'data'/'edges.csv'; data.parent.mkdir(parents=True,exist_ok=True); df.to_csv(data,index=False)
 from .template_adapter import _load_module
 m=_load_module(Path(k['repo_root'])/'05_python/templates/graph_shortest_path.py'); m.DATA_PATH=data; m.SOURCE=str(b['source']); m.TARGET=str(b['target']); m.DIRECTED=bool(b.get('directed',False)); old=Path.cwd(); os.chdir(run)
 try:m.main()
 finally:os.chdir(old)
 r=json.loads((run/'results'/'shortest_path.json').read_text()); return {'execution_mode':'numerical_template','outputs':[{'name':'distance','value':r['distance'],'unit':'path_weight'},{'name':'path','value':r['path'],'unit':'nodes'}],'metrics':{},'artifacts':[{'kind':'json','path':str(run/'results'/'shortest_path.json'),'description':'shortest path'}]}

def _trajectory(**k):
 from .template_adapter import InputBlocked
 b=dict(k.get('binding') or {}); validate_binding('mechanism_simulation',b); import pandas as pd
 p=Path(k['project_dir']).resolve(); src=Path(b['data_path']); src=src if src.is_absolute() else p/src
 if not src.exists(): raise InputBlocked(f'data_path does not exist: {src}')
 from .template_adapter import _load_module
 m=_load_module(Path(k['repo_root'])/'05_python/templates/trajectory_reconstruction.py'); df=m.read_table(src,b.get('sep')); ev,tr=m.reconstruct(df,b['entity_col'],b['time_col'],b['node_col'],b.get('max_gap_minutes')); out=Path(k['run_dir'])/'results'/'trajectory'; out.mkdir(parents=True,exist_ok=True); ep=out/'ordered_events.csv'; tp=out/'transitions.csv'; ev.to_csv(ep,index=False); tr.to_csv(tp,index=False)
 return {'execution_mode':'numerical_template','outputs':[{'name':'input_rows','value':len(df),'unit':'rows'},{'name':'transitions','value':len(tr),'unit':'events'}],'metrics':{'uncertain_gap_count':int(tr.get('gap_exceeds_limit',pd.Series(dtype=bool)).sum())},'artifacts':[{'kind':'csv','path':str(ep),'description':'ordered events'},{'kind':'csv','path':str(tp),'description':'transitions'}]}

def _echo(**k):
    """Deterministic registry smoke-test tool for the fixed entrypoint."""
    return {
        "execution_mode": "registered_echo",
        "outputs": list(k.get("outputs") or []),
        "metrics": {},
        "artifacts": [],
    }

def _expr(name):
 def h(**k):
  from .expression_adapter import optimize, monte_carlo, sensitivity
  fn={'optimization':optimize,'monte_carlo':monte_carlo,'sensitivity':sensitivity}[name]
  return {'execution_mode':'explicit_math_expression','outputs':[{'name':'result','value':fn(dict(k.get('binding') or {})),'unit':'structured'}],'metrics':{},'artifacts':[]}
 return h

def register_default_tools(registry):
 from .tool_registry import ToolSpec
 hs={'echo':_echo,'python.baseline_regression':_tab,'python.model_compare':_tab,'python.classification_cv':_tab,'python.time_series_cv':_time,'python.optimization':_expr('optimization'),'python.graph_shortest_path':_graph,'python.monte_carlo':_expr('monte_carlo'),'python.sensitivity':_expr('sensitivity'),'python.trajectory_reconstruction':_trajectory}
 for n,h in hs.items(): registry.register(ToolSpec(name=n,purpose='V0.9-C numerical adapter',handler=h,input_names=['task_id','model_id','project_dir','run_dir','binding'],output_names=['ResultBundle']))
