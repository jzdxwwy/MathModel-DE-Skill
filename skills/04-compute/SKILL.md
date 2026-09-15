# Stage 04 — Compute Skill

## 目的
把 `ModelSpec` / `ToolDispatchPlan` 转化为可复现计算，并形成 `RunManifest` 与符合契约的 `ResultBundle`。

## V0.9-B 核心原则
1. **显式绑定**：数据文件、目标列、特征列和计算参数必须来自 `ModelSpec.data_binding`；禁止根据列顺序或“最后一列”等启发式猜测目标变量。
2. **封闭工具注册表**：只能调用 `ToolRegistry` 中已注册的工具，不接受 LLM 直接生成 shell 命令。
3. **可执行与可验证分离**：模板执行成功只说明代码运行完成，不说明模型正确。
4. **失败闭合**：缺少数据绑定、格式不支持、列不存在或暂未实现对应数学输入契约时，状态为 `INPUT_BLOCKED`，不得伪造结果。
5. **真实结果可追溯**：运行目录保存模板输出、运行清单、输入绑定与 ResultBundle。

## 当前 V0.9-B 已接通模板
- `linear_regression` → `python.baseline_regression`
- `tree_ensemble_regression` → `python.model_compare`
- `logistic_classification` → `python.classification_cv`

其余已注册工具暂保持 audit adapter，待建立对应的数学输入契约后再接入真实计算。

## 数据绑定契约
```json
{
  "data_path": "附件或工作目录中的明确文件",
  "target": "明确目标列",
  "features": ["明确特征列"],
  "seed": 20260913,
  "test_size": 0.2,
  "n_splits": 5
}
```
其中后 3 项按模型适用性提供。`data_path` 与 `target` 对当前表格型模板是必需的。

## 输出
- `RunManifest`
- `ResultBundle`
- 模板原始结果文件

## Gate
`RUN_COMPLETE` ≠ 数学正确。结果必须进入 Verification Stage；`INPUT_BLOCKED` 不得进入论文结论。
