from __future__ import annotations
import re
import numpy as np
from scipy.optimize import minimize
from sympy import Abs, cos, exp, log, sin, sqrt, sympify, symbols, lambdify
from .v09c_contracts import ContractBlocked, validate_binding

FUNCS={"sin":sin,"cos":cos,"exp":exp,"log":log,"sqrt":sqrt,"Abs":Abs}
SAFE=re.compile(r"^[A-Za-z0-9_+\-*/().,=<>\[\]{}\s^%]+$")

def _expr(text,names):
    if not isinstance(text,str) or not text.strip() or not SAFE.fullmatch(text) or "__" in text or ";" in text or "import" in text.lower() or "lambda" in text.lower():
        raise ContractBlocked("unsupported expression syntax")
    local={n:symbols(n) for n in names}|FUNCS
    try: return sympify(text.replace("^","**"),locals=local)
    except Exception as e: raise ContractBlocked(f"invalid mathematical expression: {e}") from e

def optimize(b):
    validate_binding("optimization",b); names=list(map(str,b["variables"]))
    if len(names)!=len(b["bounds"]): raise ContractBlocked("variables/bounds dimension mismatch")
    f=lambdify(symbols(names),_expr(b["objective_expression"],names),"numpy")
    cs=[]
    for text in b.get("inequality_constraints",[]):
        cf=lambdify(symbols(names),_expr(text,names),"numpy"); cs.append({"type":"ineq","fun":lambda x,cf=cf:float(cf(*x))})
    bounds=[(float(x[0]),float(x[1])) for x in b["bounds"]]; x0=b.get("initial_point") or [sum(x)/2 for x in bounds]
    r=minimize(lambda x:float(f(*x)),np.asarray(x0,float),method="SLSQP",bounds=bounds,constraints=cs)
    if not r.success: raise RuntimeError(r.message)
    return {"method":"SLSQP","variables":names,"x":r.x.tolist(),"objective":float(r.fun),"success":bool(r.success)}

def sensitivity(b):
    validate_binding("sensitivity",b); base={str(k):float(v) for k,v in b["base"].items()}; names=list(base)
    f=lambdify(symbols(names),_expr(b["objective_expression"],names),"numpy"); base_y=float(f(*[base[n] for n in names])); rows=[]
    for n in names:
        for v in map(float,b["grid"]):
            p=base.copy(); p[n]=v; y=float(f(*[p[x] for x in names])); rows.append({"parameter":n,"value":v,"objective":y,"delta":y-base_y})
    rank={n:max(abs(r["delta"]) for r in rows if r["parameter"]==n) for n in names}
    return {"baseline_objective":base_y,"rows":rows,"ranking":dict(sorted(rank.items(),key=lambda x:x[1],reverse=True))}

def monte_carlo(b):
    validate_binding("monte_carlo",b); names=list(map(str,b["variables"])); f=lambdify(symbols(names),_expr(b["event_expression"],names),"numpy"); rng=np.random.default_rng(int(b["seed"])); n=int(b["n"]); s={}
    for name in names:
        d=b["distributions"].get(name,{}); typ=d.get("name","").lower()
        if typ=="normal": s[name]=rng.normal(float(d["mean"]),float(d["std"]),n)
        elif typ=="uniform": s[name]=rng.uniform(float(d["low"]),float(d["high"]),n)
        elif typ=="exponential": s[name]=rng.exponential(float(d["scale"]),n)
        else: raise ContractBlocked(f"unsupported distribution: {typ}")
    p=float((np.asarray(f(*[s[x] for x in names]))>0).mean()); se=float(np.sqrt(p*(1-p)/n)); return {"n":n,"estimate":p,"standard_error":se,"CI95":[max(0,p-1.96*se),min(1,p+1.96*se)]}
