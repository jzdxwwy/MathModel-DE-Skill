"""Generic Monte Carlo template for probability/reliability D problems."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

SEED = 20260913
N = 100_000


def simulation(rng: np.random.Generator, size: int) -> np.ndarray:
    # Replace this toy event with the actual model event indicator (0/1).
    x = rng.normal(size=size)
    return (x > 1.645).astype(int)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    rng = np.random.default_rng(SEED)
    event = simulation(rng, N)
    p = float(event.mean())
    se = float(np.sqrt(p * (1 - p) / N))
    ci = [max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se)]
    out = Path("results"); out.mkdir(exist_ok=True)
    manifest = {
        "run_id": "monte-carlo",
        "problem": "DE-template",
        "question": "Q1",
        "python": sys.version,
        "seed": SEED,
        "model": "Monte-Carlo",
        "parameters": {"N": N},
        "command": "python 05_python/templates/monte_carlo.py",
        "outputs": [str(out / "monte_carlo_manifest.json")],
        "status": "RUN_COMPLETE",
        "notes": json.dumps({"estimate": p, "standard_error": se, "CI95": ci}, ensure_ascii=False),
    }
    (out / "monte_carlo_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
