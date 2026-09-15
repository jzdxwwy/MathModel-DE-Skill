# V0.9-C Mathematical Contracts

V0.9-B 解决“如何安全调用 Python”；V0.9-C 解决“数学模型需要哪些可计算输入”。

| Model | Required inputs | Adapter |
|---|---|---|
| time_series_baseline | data_path, time_col, target | rolling-origin Ridge |
| shortest_path | data_path, source, target | Dijkstra |
| mechanism_simulation | data_path, entity_col, time_col, node_col | trajectory reconstruction |
| optimization | objective_expression, variables, bounds | SLSQP |
| sensitivity | objective_expression, base, grid | OAT |
| monte_carlo | event_expression, variables, distributions, n, seed | Monte Carlo |

## Rules
1. Data facts come from DataProfile; semantic bindings come from ModelSpec/LLM proposal; Schema/Gate decides acceptance.
2. Mathematical expressions are not Python code.
3. Missing required inputs must produce INPUT_BLOCKED.
4. Template toy objectives/events must never be presented as contest results.
5. ResultBundle stores only actually computed values and artifact references.

V0.9-C does not decide whether a contest formula is mathematically correct; that remains the Verification Stage. Its responsibility is to guarantee that explicit, structured, auditable mathematical inputs are either computed or clearly blocked.
