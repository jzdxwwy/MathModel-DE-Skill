# 05 Python：可复现求解层

本目录把“模型 → 代码 → 结果”固定成可追溯链条。

## 模板

| 模板 | 用途 | 默认定位 |
|---|---|---|
| `templates/baseline_regression.py` | Ridge回归、MAE/RMSE/R² | E题基线 |
| `templates/time_series_cv.py` | 滚动时间验证 | E题时间序列 |
| `templates/monte_carlo.py` | 概率/可靠性仿真 | D题 |
| `templates/sensitivity.py` | 单因素敏感性 | D/E通用 |

模板中的 toy objective / toy event 只是可运行占位，正式比赛必须替换成题目模型；不能把模板输出冒充题目结果。

## 标准顺序

1. 原始附件只读。
2. 数据审计。
3. 建立问题配置：变量、单位、参数、约束、随机种子。
4. 先跑 baseline。
5. 实现主模型并记录参数。
6. 保存中间结果、最终结果和图表数据。
7. 做独立验证。
8. 将关键数字冻结到 `frozen_numbers.json`。
9. 论文只引用冻结数字。

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
