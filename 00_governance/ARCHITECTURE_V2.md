# MathModel-DE-Skill v2 架构设计

> 状态：Architecture Baseline v2.0
> 
> 本文定义 `MathModel-DE-Skill` 从“知识/工具箱”升级为“Artifact-driven Workflow Skill”的总体架构。

## 1. 项目定位

本项目不是 D/E 历年题答案集合，也不是 Python 模型模板集合，而是一套可复用、可验证、可回归测试的 CUMCM D/E 数学建模工作流 Skill。

核心目标：

```text
题目/附件
  → 问题理解
  → 问题结构化
  → 数据/机理分析
  → 候选模型
  → 模型选择
  → 计算求解
  → 验证
  → 可视化
  → 论文证据
  → 最终论文
```

其中各阶段通过结构化 Artifact 传递状态，而不是依赖自然语言上下文“猜测”前一阶段做了什么。

## 2. 三层架构

### 2.1 Workflow Layer：工作流层

负责“什么时候做什么”。

```text
Master Skill
   ├── Start
   ├── Analysis
   ├── Data
   ├── Modeling
   ├── Compute
   ├── Visualization
   ├── Verification
   └── Writing
```

每个 Stage Skill 必须定义：

- 输入 Artifact
- 前置条件
- 执行任务
- 输出 Artifact
- Gate
- 失败处理
- 可调用工具

### 2.2 Knowledge/Tool Layer：知识与工具层

负责“知道什么、能算什么”。

包括：

- D/E 题型知识
- 问题类型知识
- 模型选择知识
- 统计/优化/仿真/网络/机器学习等模型知识
- Python 模板
- 可视化工具
- 文档生成工具

知识和工具不得反向定义主工作流。

### 2.3 Evaluation Layer：评价层

负责“做得对不对”。

包括：

- Stage Gates
- Final Gate
- Artifact Schema 校验
- Smoke Test
- Regression Benchmark
- 数值一致性与可复现性检查

## 3. Master Skill 职责

根目录 `SKILL.md` 是 Master Skill，不承担全部建模知识。

Master Skill 负责：

1. 判断当前工作模式：Skill Development / Benchmark / Problem Solving；
2. 创建项目运行计划；
3. 确定当前阶段；
4. 调用相应 Stage Skill；
5. 检查阶段 Artifact 是否完整；
6. 在 Gate 未通过时阻止无条件进入下一阶段；
7. 维护 run manifest、todo 和阶段状态；
8. 最终汇总验证结果并交给 Writing Stage。

## 4. Stage Skills

| Stage | 职责 | 核心输出 |
|---|---|---|
| 00-start | 建立项目、读取题目、确定模式和计划 | ProblemSpec、项目计划 |
| 01-analysis | 拆题、识别变量、约束、任务类型 | ProblemMap |
| 02-data | 附件体检、数据质量、变量关系、EDA | DataProfile |
| 03-modeling | 候选模型、模型比较、主模型设计 | ModelPlan、ModelSpec |
| 04-compute | 编码、参数估计、求解、结果整理 | RunManifest、ResultBundle |
| 05-visualization | 从真实结果生成论文图表 | FigureBundle / PaperEvidence |
| 06-verification | 数值、逻辑、边界、敏感性、稳健性验证 | VerificationReport |
| 07-writing | 将已验证结果转化为论文内容 | PaperEvidence、论文草稿 |

## 5. Artifact 主数据流

```text
ProblemSpec
    ↓
ProblemMap
    ↓
DataProfile
    ↓
ModelPlan
    ↓
ModelSpec
    ↓
RunManifest
    ↓
ResultBundle
    ↓
VerificationReport
    ↓
PaperEvidence
```

### 关键原则

- 下游阶段优先消费上游 Artifact，而不是重新猜测原始题意。
- Artifact 必须包含来源、状态和版本信息。
- 核心数值必须可追溯到 RunManifest 或输入数据。
- Writing Stage 不得自行生成未经验证的核心结果。

## 6. D/E 的架构定位

D/E 不再作为两条独立主流程，而作为问题识别与模型选择的先验知识。

```text
题目
 ↓
问题任务识别
 ↓
预测 / 评价 / 优化 / 分类 / 聚类 / 仿真 / 网络 / 风险 / 综合决策...
 ↓
结合 D/E 先验缩小候选范围
 ↓
模型选择
```

因此：

- D/E 是 domain prior；
- 问题类型是 workflow 的核心分类；
- 模型族是知识层；
- Stage Skill 是执行层。

## 7. Gate 体系

验证不是最后一步才发生，而是贯穿工作流。

```text
Analysis Gate
   ↓
Data Gate
   ↓
Model Gate
   ↓
Compute Gate
   ↓
Verification Gate
   ↓
Writing Gate
   ↓
Final Gate
```

任何关键 Gate 未通过，不得将项目状态标记为完成。

## 8. Benchmark / Regression 定位

历史题是能力测试源，而不是架构定义源。

Benchmark 应描述：

- 输入；
- 要测试的能力；
- 必须生成的 Artifact；
- 检查规则；
- 数值/结构容差；
- Regression 结果。

2024D/E、2025D/E 用于验证 Skill 的泛化和防退化能力。

## 9. 工具层原则

Python、优化器、绘图库、文档工具均属于工具层。

工具由 Stage Skill 按 ModelSpec/任务需要调用，不允许“因为已有模板所以强行使用模型”。

## 10. v2 设计判据

新增任何文件或能力前，应回答：

1. 它属于 Workflow、Knowledge、Tool 还是 Evaluation？
2. 它服务哪个 Stage？
3. 它消费哪个 Artifact？
4. 它产生哪个 Artifact？
5. 是否可以被另一道 D/E 题复用？
6. 是否有验证方式？

若无法回答，应暂缓加入主架构。
