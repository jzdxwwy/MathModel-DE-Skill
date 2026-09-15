# V0.9-B — Template Adapter Layer

## 目标
将 V0.9 的“可执行 Tool Boundary”升级为“可执行数学模板”，建立统一链路：

`DataProfile → explicit data_binding → ToolRegistry → Python Template → ResultBundle`

## 为什么不让模板自己猜数据
CUMCM 附件结构高度异构。自动把“最后一列”当目标、把某个 Excel sheet 当数据源或根据列名模糊匹配，都可能产生看似正常但实际错误的结果。因此 V0.9-B 要求：

- `data_path` 必须明确；
- `target` 必须明确；
- `features` 可以显式给出，留空时只允许使用“除 target 外全部列”这一确定规则；
- 缺失或冲突时 `INPUT_BLOCKED`；
- LLM 可以提出 binding，但不能覆盖确定性模型选择，也不能凭空创建字段。

## 当前接入
1. `linear_regression` → `baseline_regression.py`
2. `tree_ensemble_regression` → `model_compare.py`
3. `logistic_classification` → `classification_cv.py`

这些模板原本使用模块级常量。V0.9-B 通过受控模块加载后覆盖 `DATA_PATH/TARGET/FEATURES`，不修改原模板源码，保持模板可独立运行。

## ResultBundle 修正
V0.9 初版曾把内部 adapter 返回值写入 `results`。但 `result-bundle.schema.json` 的正式契约使用 `outputs / metrics / artifacts / provenance`。V0.9-B 已按该契约输出，避免“运行成功但产物不符合 Schema”。

## 验收
新增：
- `tests/runtime/test_v09_b_template_adapter.py`
- `tests/runtime/test_v09_b_execution_engine.py`
- `tests/fixtures/v09_b_regression.csv`

当前环境没有执行测试，因此提交记录只证明代码与测试文件已经写入仓库，不能宣称测试通过。下一步应在具备 Python 依赖的运行环境执行测试，并将结果纳入回归门禁。

## 下一阶段
V0.9-C：
- 把 `time_series_cv / optimization / graph_shortest_path / monte_carlo / sensitivity / trajectory_reconstruction` 分别建立独立输入契约；
- 每个工具返回标准化数值结果与验证指标；
- 增加 ResultBundle Schema 自动校验；
- 再进入 Verification Stage 的自动验收。
