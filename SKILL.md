# MathModel-DE-Skill Master Skill

> 面向 CUMCM D/E 题的可复用数学建模 Workflow Skill。
>
> 本文件是 **Master Skill / Orchestrator**，负责调度工作流；具体知识和工具由 Stage Skills、Knowledge、Tools 提供。

## 1. 核心定位

本 Skill 不把数学建模理解为“选择一个模型并写 Python”，而是建立一条可追踪、可验证、可回归测试的工作流：

```text
题目/附件
→ ProblemSpec
→ ProblemMap
→ DataProfile
→ ModelPlan
→ ModelSpec
→ Compute
→ ResultBundle
→ VerificationReport
→ PaperEvidence
→ 论文
```

阶段之间通过 Artifact Contract 传递状态。详见：

- `00_governance/ARCHITECTURE_V2.md`
- `artifacts/ARTIFACT_CONTRACTS.md`

## 2. Master Skill 的职责

Master Skill 负责：

1. 判断当前工作模式；
2. 创建项目计划与任务清单；
3. 识别当前阶段；
4. 调用对应 Stage Skill；
5. 检查上游 Artifact 是否存在且状态有效；
6. 检查阶段 Gate；
7. 允许或阻止进入下一阶段；
8. 维护运行记录和结果追溯关系；
9. 最终把已验证证据交给 Writing Stage。

Master Skill **不承担全部模型知识**，也不应该直接堆叠 Python 模板。

## 3. 三种工作模式

### A. Skill Development（默认）

目标是增强本仓库本身：

```text
历史题/案例
→ 能力缺口
→ 通用抽象
→ Skill/Knowledge/Tool
→ Benchmark
→ Test
→ Regression
```

### B. Benchmark / Regression Test

使用历史题检验 Skill 是否退化。历史题是测试源，不是架构定义源。

### C. Problem Solving

只有用户明确要求解某道题时才进入。此时以题目最终结果、数值结果和论文为目标，但仍必须遵守 Artifact、验证和追溯规则。

## 4. 标准 Stage Workflow

### Stage 00 — Start

输入：题目、附件、用户要求。

输出：`ProblemSpec`、项目计划、todo。

任务：确认工作模式、读取题目与附件、区分显式要求与待推断信息、建立问题编号。

### Stage 01 — Analysis

输入：`ProblemSpec`。

输出：`ProblemMap`。

任务：拆分问题、识别任务类型、定义变量/输入/输出/约束、建立子问题依赖关系、形成候选方法族。

### Stage 02 — Data

输入：`ProblemSpec`、`ProblemMap`、附件。

输出：`DataProfile`。

任务：数据体检、schema/单位检查、缺失/重复/异常检查、时间/空间/实体关系检查、EDA、预处理建议。

### Stage 03 — Modeling

输入：`ProblemMap`、`DataProfile`。

输出：`ModelPlan`、`ModelSpec`。

任务：候选模型、可解释 baseline、模型比较、升级理由、假设/目标函数/方程/约束/参数来源/验证方案。

### Stage 04 — Compute

输入：`ModelSpec`、`DataProfile`。

输出：`RunManifest`、`ResultBundle`。

任务：编码、参数估计、求解/预测/仿真、记录环境/参数/随机种子/输入、保存原始结果与关键数字。

### Stage 05 — Visualization

输入：`ResultBundle`、必要的 `DataProfile`。

输出：图表及 `PaperEvidence` 的图表证据。

任务：只从真实结果生成图表，标注单位/来源/指标，图表追溯到 run_id/result 文件。

### Stage 06 — Verification

输入：`ModelSpec`、`RunManifest`、`ResultBundle`。

输出：`VerificationReport`。

任务：公式与单位检查、可行性/边界检查、残差/误差/预测验证、数据泄漏检查、敏感性/稳健性、可复现性。

### Stage 07 — Writing

输入：已通过验证的 `PaperEvidence`。

输出：论文草稿/最终论文材料。

任务：把模型、计算、验证和结论组织为论文；不自行发明核心数字；重要结论关联模型、结果和验证依据。

## 5. Gate 原则

工作流采用逐阶段质量门禁：

```text
Analysis Gate
→ Data Gate
→ Model Gate
→ Compute Gate
→ Verification Gate
→ Writing Gate
→ Final Gate
```

任何关键 Gate 未通过，不得把项目标记为完成。

最终质量要求继续由 `08_verification/Final_Gate.md` 负责。

## 6. D/E 的定位

D/E 不是两条独立主流程，而是领域先验。首先判断任务类型：prediction、evaluation、optimization、classification、clustering、simulation、mechanism、network、risk、comprehensive_decision，再结合 D/E 先验缩小候选模型空间。

D 题常见先验：机理、概率与不确定性、优化、多目标、动力/传播/仿真、网络/路径、敏感性/稳健性等。

E 题常见先验：数据清洗、EDA、特征工程、回归、分类、时间序列、聚类、降维、综合评价、机器学习、决策优化等。

**禁止因为题目被标记为 D/E，就直接套用对应模型清单。**

## 7. 模型选择总原则

1. 先理解问题，再选择模型；
2. 优先建立可解释、可验证 baseline；
3. 复杂模型必须有明确升级理由；
4. 数据量不足、约束无法满足、存在泄漏或结果无法验证时，不得强行使用复杂模型；
5. 候选模型必须说明选择依据；
6. 每个核心模型至少说明：适用条件、假设、变量、参数来源、求解方法、验证方法、局限性。

## 8. 可追溯与真实性

- 不得虚构数据、参数、实验结果、文献或竞赛结论；
- 核心数字必须能够追溯到输入、Artifact 或 RunManifest；
- 图表必须来自真实计算；
- 不得把相关性直接写成因果关系；
- 不得把模型输出直接等同于现实规律；
- 不得为了增加模型数量而堆叠无意义算法。

## 9. 工具调用原则

工具不是工作流的上层架构。

```text
Stage Skill
    ↓
判断需要什么能力
    ↓
选择 Knowledge / Python / Visualization / Document Tool
    ↓
生成或更新 Artifact
```

因此新增 Python 模板前必须证明它是通用能力，并明确输入、输出、适用问题、调用 Stage、验证方式、smoke test / regression test。

## 10. 历史题与 Benchmark

2024D/E、2025D/E 等历史题用于能力缺口发现、benchmark、regression test、泛化能力测试和案例知识提取。不得因为某一道历史题出现某种方法，就把该方法硬编码成主流程。

## 11. Runtime 执行层

Master Skill 已具备 V0.6-C 的模型可执行运行时边界：

```text
External Host / CLI
        ↓ HostRequest
RealLLMHostAdapter
        ↓ ModelAdapter
OpenAI-compatible LLM endpoint
        ↓ ModelResponse
RuntimeOrchestrator
        ↓
TaskContext + Stage Skills + Tools + Gates
        ↓
Artifacts
```

当前 Runtime 已支持：

- `tools/runtime/model_adapter.py`：Provider-neutral ModelAdapter；
- `tools/runtime/llm_config.py`：环境变量配置，禁止在仓库保存密钥；
- `tools/runtime/providers/openai_compatible.py`：标准库 HTTP 的 OpenAI-compatible 适配器；
- `tools/runtime/real_host.py`：真实 LLM Host；
- `tools/runtime/entrypoint.py`：`--host demo|real`；
- `tools/runtime/orchestrator.py`：持久化每阶段实际模型输出；
- `tools/runtime/V0_6_C_REAL_LLM.md`：配置与运行说明。

V0.6-C 的边界是**真实模型调用已经打通，但尚未声称完整 CUMCM 自动求解**。后续仍需完成真实附件摄取、结构化 Artifact 自动生成、Tool Dispatch、计算求解、独立验证和论文证据流水线。

## 12. 当前实现状态

v2 第一阶段已经建立 Master/Stage 架构、Artifact Contract、JSON Schema、Gate、Traceability、Workflow Engine、E2E Demo，以及 V0.6 Model-Executable Runtime。当前进一步完成 V0.6-C Real LLM Host Adapter。

下一阶段优先推进 **V0.7：真实题目与附件摄取 + ProblemSpec/DataProfile 自动构建**，并继续保持 Artifact/Gate/Traceability 为运行时权威边界。
