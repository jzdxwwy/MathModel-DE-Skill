# V0.8 — 自动模型选择与 Tool Dispatch

## 目标
把 V0.7-B 的 `ProblemSpec → ProblemMap → DataProfile` 继续向可执行建模推进，形成：

`任务分类 → 候选模型 → 硬约束淘汰 → 七维评分 → ModelPlan → ModelSpec/ModelComparison → ToolDispatchPlan`

## 核心原则
- 确定性选择器是权威层，LLM 是语义补充层。
- D/E 是先验，不是两条固定流水线。
- 选择分数不是拟合指标；真实计算指标在 V0.9 产生。
- 工具调度采用封闭目录，LLM 不能任意发明工具名。
- V0.8 只规划，不执行数值计算。

## 产物
- `model-plan.json`
- `model-spec/<task_id>.json`
- `model-comparison-<task_id>.json`
- `tool-dispatch.json`

## 下一阶段
V0.9 将消费 `ToolDispatchPlan`，生成 `RunManifest + ResultBundle`，真正调用 Python/优化/统计/仿真工具并进入 Verification Gate。
