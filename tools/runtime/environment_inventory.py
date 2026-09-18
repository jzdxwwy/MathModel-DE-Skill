"""V1.0-J host-owned environment inventory collector.

Executed only through a fixed module entrypoint; it does not execute model
supplied code or commands.
"""
from __future__ import annotations
import hashlib, json, platform, sys
from importlib import metadata
from pathlib import Path
from typing import Any

def _canonical(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",",":"), default=str)

def collect_inventory(interpreter: str | None = None) -> dict[str, Any]:
    packages = [{"name": d.metadata.get("Name", d.name), "version": d.version} for d in metadata.distributions()]
    packages = sorted(packages, key=lambda x:(x["name"].lower(), x["version"]))
    body = {
        "artifact_type":"EnvironmentInventory",
        "schema_version":"1.0-J",
        "interpreter":interpreter or sys.executable,
        "python":{"implementation":platform.python_implementation(),"version":platform.python_version()},
        "packages":packages,
    }
    body["fingerprint"] = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
    return body

def persist_inventory(path: str | Path, interpreter: str | None = None) -> Path:
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(collect_inventory(interpreter),ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    return p

if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    parser.add_argument("--interpreter",default=None)
    args=parser.parse_args()
    persist_inventory(args.output,args.interpreter)
