# Stage 03 — Modeling Skill

## 目的
基于 `ProblemSpec + ProblemMap + DataProfile` 自动形成可解释、可验证、可追溯的模型方案。

## V0.8 执行顺序
1. 按任务 `task_id` 分类任务类型。
2. 从封闭模型目录生成候选模型。
3. 先做硬约束淘汰：数据不足、约束冲突、明显泄漏风险、无法验证。
4. 使用七维权重评分：fit 25 / data 15 / constraints 15 / interpretability 15 / verifiability 15 / robustness 10 / cost 5。
5. 保留 baseline 与至少一个可比较备选。
6. 形成 `ModelPlan`、逐任务 `ModelSpec` 与 `ModelComparison`。
7. LLM 可以提出语义解释，但不能覆盖确定性选择结果，也不能虚构数据、参数或计算指标。

## D/E 定位
D/E 仅作为模型选择先验，不是固定工作流。实际选择首先由任务结构、数据条件和验证条件决定。

## 输出
- `artifacts/model-plan.json`
- `artifacts/model-spec/<task_id>.json`
- `artifacts/model-comparison-<task_id>.json`

## Gate
模型必须可解释、可验证并具有数据/问题结构依据；V0.8 的 comparison score 是选择分，不是假装的拟合性能。真实误差、交叉验证等计算指标留给 V0.9。
