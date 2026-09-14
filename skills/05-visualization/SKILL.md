# Stage 05 — Visualization Skill

## 目的
把真实计算结果转化为可追溯的论文级图表。

## 输入
`ResultBundle` 与必要的 `DataProfile`。

## 核心规则
- 图表来自真实数据/真实计算；
- 坐标轴、单位、图例完整；
- 图表必须能追溯到 run_id 或结果文件；
- 不用示意图冒充计算结果。

## 输出
- figures
- 图表证据，供 `PaperEvidence` 使用

## Gate
没有真实结果来源的图表不得进入论文。
