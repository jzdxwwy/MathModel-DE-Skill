"""Dijkstra shortest-path template for D graph/network problems.

Input CSV columns: u,v,weight. Nodes are treated as strings.
For directed networks set DIRECTED=True; otherwise edges are bidirectional.
"""
from pathlib import Path
import hashlib
import json
import heapq
import sys
import pandas as pd

DATA_PATH = Path("data/edges.csv")
SOURCE = "A"
TARGET = "Z"
DIRECTED = False


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_graph(df):
    graph = {}
    for row in df.itertuples(index=False):
        u, v, w = str(row.u), str(row.v), float(row.weight)
        if w < 0:
            raise ValueError("Dijkstra requires non-negative edge weights")
        graph.setdefault(u, []).append((v, w))
        if not DIRECTED:
            graph.setdefault(v, []).append((u, w))
    return graph


def dijkstra(graph, source, target):
    dist = {source: 0.0}
    prev = {}
    pq = [(0.0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if d != dist.get(u):
            continue
        if u == target:
            break
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    if target not in dist:
        raise ValueError(f"No path from {source} to {target}")
    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    path.reverse()
    return dist[target], path


def main():
    df = pd.read_csv(DATA_PATH)
    required = {"u", "v", "weight"}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV must contain {sorted(required)}")
    graph = build_graph(df)
    distance, path = dijkstra(graph, SOURCE, TARGET)
    out = Path("results"); out.mkdir(exist_ok=True)
    result = {"source": SOURCE, "target": TARGET, "distance": distance, "path": path}
    (out / "shortest_path.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "run_id": "dijkstra-shortest-path",
        "problem": "DE-template",
        "question": "Q1",
        "input_hash": sha256_file(DATA_PATH),
        "python": sys.version,
        "model": "Dijkstra",
        "parameters": {"directed": DIRECTED, "source": SOURCE, "target": TARGET},
        "command": "python 05_python/templates/graph_shortest_path.py",
        "outputs": ["results/shortest_path.json"],
        "status": "RUN_COMPLETE",
        "notes": "Use time-expanded/network-flow models instead when edge costs or node states vary with time.",
    }
    (out / "shortest_path_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
