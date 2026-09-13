"""Generic Monte Carlo template for probability/reliability D problems."""
from pathlib import Path
import json
import numpy as np

SEED = 20260913
N = 100_000


def simulation(rng: np.random.Generator, size: int) -> np.ndarray:
    # Replace this toy event with the actual model event indicator (0/1).
    x = rng.normal(size=size)
    return (x > 1.645).astype(int)


def main():
    rng = np.random.default_rng(SEED)
    event = simulation(rng, N)
    p = float(event.mean())
    se = float(np.sqrt(p * (1 - p) / N))
    ci = [max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se)]
    out = Path("results"); out.mkdir(exist_ok=True)
    manifest = {"template":"monte_carlo", "seed":SEED, "N":N, "estimate":p, "standard_error":se, "CI95":ci, "status":"RUN_COMPLETE"}
    (out / "monte_carlo_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
