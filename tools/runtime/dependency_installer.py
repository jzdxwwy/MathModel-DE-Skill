"""V1.0-J controlled dependency installer.

Only fixed-argv subprocesses are used. The module never accepts a shell command
string. Network access is disabled by default; a local wheelhouse is required
when packages must be installed under the default policy.
"""
from __future__ import annotations
import hashlib, json, os, re, subprocess, sys
from pathlib import Path
from typing import Any

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+!_-]*$")

def _canonical(v: Any) -> str:
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=str)

def _hash_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def _validate_package(p: dict[str,Any]) -> None:
    if not _NAME_RE.fullmatch(str(p.get("name",""))): raise ValueError("invalid locked package name")
    if not _VERSION_RE.fullmatch(str(p.get("version",""))): raise ValueError("invalid locked package version")
    if "hash" in p and not re.fullmatch(r"^[a-f0-9]{64}$",str(p["hash"])): raise ValueError("invalid package hash")

def _pip(interpreter: Path, args: list[str], *, env: dict[str,str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(interpreter),"-m","pip",*args],shell=False,check=False,capture_output=True,text=True,env=env)

def install_locked_dependencies(contract: dict[str,Any], *, output_dir: str|Path) -> dict[str,Any]:
    if contract.get("artifact_type")!="DependencyMaterializationContract" or contract.get("schema_version")!="1.0-J":
        raise ValueError("invalid DependencyMaterializationContract")
    policy=contract.get("policy",{})
    if policy.get("allow_network") is not False or policy.get("allow_shell") is not False:
        raise PermissionError("network and shell must be disabled")
    interpreter=Path(str(contract["interpreter"])).resolve()
    if not interpreter.is_file(): raise FileNotFoundError(f"venv interpreter missing: {interpreter}")
    packages=contract.get("packages",[])
    wheelhouse=Path(str(contract.get("wheelhouse",""))).resolve() if contract.get("wheelhouse") else None
    if packages and not wheelhouse:
        raise ValueError("a local wheelhouse is required when network is disabled")
    if wheelhouse and not wheelhouse.is_dir(): raise FileNotFoundError("wheelhouse does not exist")
    env=dict(os.environ)
    env["PIP_DISABLE_PIP_VERSION_CHECK"]="1"
    env["PIP_NO_INPUT"]="1"
    # First bootstrap pip from the interpreter's bundled ensurepip; no network is used.
    boot=subprocess.run([str(interpreter),"-m","ensurepip","--upgrade"],shell=False,check=False,capture_output=True,text=True,env=env)
    if boot.returncode!=0:
        return {"status":"FAILED","reason":"ensurepip failed","stdout":boot.stdout[-4000:],"stderr":boot.stderr[-4000:]}
    requirements=[]
    for p in packages:
        _validate_package(p)
        line=f'{p["name"]}=={p["version"]}'
        if policy.get("require_hashes") and "hash" not in p:
            return {"status":"FAILED","reason":f'missing required hash for {p["name"]}'}
        if "hash" in p: line += f' --hash=sha256:{p["hash"]}'
        requirements.append(line)
    req=Path(output_dir).resolve()/"locked-requirements.txt"
    req.parent.mkdir(parents=True,exist_ok=True)
    req.write_text("\n".join(requirements)+"\n",encoding="utf-8")
    args=["install","--no-index","--disable-pip-version-check","--no-input","--requirement",str(req)]
    if wheelhouse: args += ["--find-links",str(wheelhouse)]
    if policy.get("require_hashes"): args += ["--require-hashes"]
    result=_pip(interpreter,args,env=env)
    if result.returncode!=0:
        return {"status":"FAILED","reason":"locked dependency installation failed","stdout":result.stdout[-4000:],"stderr":result.stderr[-4000:],"requirements_sha256":_hash_file(req)}
    return {"status":"INSTALLED","requirements":str(req),"requirements_sha256":_hash_file(req),"stdout":result.stdout[-4000:],"stderr":result.stderr[-4000:]}
