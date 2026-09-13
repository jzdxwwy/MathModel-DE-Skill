# 05 Python：可复现求解层

本目录把“模型 → 代码 → 结果”固定成可追溯链条。

## 模板

| 模板 | 用途 | 默认定位 |
|---|---|---|
| `templates/baseline_regression.py` | Ridge回归、MAE/RMSE/R² | E题基线 |
| `templates/model_compare.py` | Ridge / Random Forest / Gradient Boosting 候选比较 | E题模型筛选 |
| `templates/classification_cv.py` | Logistic分类 + StratifiedKFold | E题分类 |
| `templates/time_series_cv.py` | 滚动时间验证 | E题时间序列 |
| `templates/monte_carlo.py` | 概率/可靠性仿真 | D题 |
| `templates/sensitivity.py` | 单因素敏感性 | D/E通用 |
| `templates/graph_shortest_path.py` | Dijkstra最短路径 | D题网络/路径 |
| `templates/optimization.py` | SLSQP约束优化 | D/E优化 |

模板中的 toy objective / toy event 只是可运行占位，正式比赛必须替换成题目模型；不能把模板输出冒充题目结果。

## 模板选择建议

- **D题**：先看是否存在随机风险、动态传播、网络路径、资源分配或参数优化；分别考虑 Monte Carlo、图算法、动力/仿真和优化模板。
- **E题**：先做数据体检，再跑回归/分类基线；若有时间结构使用滚动验证；候选模型比较后再决定主模型。
- **模型比较不是自动选冠军**：RMSE/Accuracy等指标只用于筛选，最终还要结合题意、约束、解释性、稳定性和验证结果。

## 标准顺序

1. 原始附件只读。
2. 数据审计。
3. 建立问题配置：变量、单位、参数、约束、随机种子。
4. 先跑 baseline。
5. 实现候选模型并记录参数。
6. 比较模型并确定主模型/备选模型。
7. 保存中间结果、最终结果和图表数据。
8. 做独立验证、敏感性或稳健性分析。
9. 将关键数字冻结到 `frozen_numbers.json`。
10. 论文只引用冻结数字。

## Run Manifest

每次正式运行建议记录 `schemas/run-manifest.schema.json` 中的字段：输入版本/哈希、Python与依赖版本、seed、模型、参数、命令、输出、状态。

推荐状态：

`RUNNING → RUN_COMPLETE → FINAL`

如果模型或数据发生变化，旧结果标记 `SUPERSEDED`，不得覆盖历史证据。

## 冻结数字

`schemas/frozen-numbers.schema.json` 定义论文数字的最小证据结构。一个冻结数字至少要知道：**数值、单位、来源 Run、论文位置**。

## 硬规则

- 禁止把手算、猜测或聊天中出现的数字写进最终结果。
- 随机算法必须固定并记录 seed。
- 时间序列禁止随机打乱训练/验证集。
- 同一对象多条记录时，优先 GroupKFold / Group split。
- 优化必须检查约束可行性。
- 仿真必须报告重复次数、随机种子和稳定性。
- 代码没有真实运行，就只能标记“待运行”。
- 历史题测试可以使用公开题目与附件；真实竞赛时必须遵守当届竞赛的AI使用、独立作答和信息隔离规定。

## Smoke Test

仓库提供 `tests/smoke_test.py`，只使用合成数据，验证上述 8 个模板能启动、产出结果并生成统一 Manifest。它不是对任何历年题答案的正确性证明。
