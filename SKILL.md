# MathModel-DE-Skill Master Skill

> 面向 CUMCM D/E 题的可复用数学建模 Workflow Skill。
>
> 本文件是 **Master Skill / Orchestrator**，负责调度工作流；具体知识和工具由 Stage Skills、Knowledge、Tools 提供。

## 1. 核心定位

本 Skill 不把数学建模理解为“选择一个模型并写 Python”，而是建立一条可追踪、可验证、可回归测试的工作流：

```text
题目/附件 → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Compute → ResultBundle → VerificationReport → PaperEvidence → 论文
```

阶段之间通过 Artifact Contract 传递状态。详见 `00_governance/ARCHITECTURE_V2.md`、`artifacts/ARTIFACT_CONTRACTS.md`。

## 2. Master Skill 的职责

1. 判断当前工作模式；2. 创建项目计划与任务清单；3. 识别当前阶段；4. 调用对应 Stage Skill；5. 检查上游 Artifact；6. 检查阶段 Gate；7. 控制阶段流转；8. 维护运行记录和结果追溯；9. 将已验证证据交给 Writing Stage。

## 3. 三种工作模式

### A. Skill Development（默认）
历史题/案例 → 能力缺口 → 通用抽象 → Skill/Knowledge/Tool → Benchmark → Test → Regression。

### B. Benchmark / Regression Test
历史题是测试源，不是架构定义源。

### C. Problem Solving
只有用户明确要求解某道题时才进入；仍必须遵守 Artifact、验证和追溯规则。

## 4. 标准 Stage Workflow

- **00 Start**：题目与附件摄取，输出 ProblemSpec。
- **01 Analysis**：问题拆分、任务结构、变量/输入/输出/约束，输出 ProblemMap。
- **02 Data**：数据体检、schema/单位、缺失/重复/异常、EDA 与预处理，输出 DataProfile。
- **03 Modeling**：候选模型、baseline、比较、假设/方程/约束/验证方案，输出 ModelPlan/ModelSpec。
- **04 Compute**：编码、求解/预测/仿真、运行记录，输出 RunManifest/ResultBundle。
- **05 Visualization**：从真实结果生成图表和 PaperEvidence。
- **06 Verification**：公式、单位、可行性、误差、泄漏、敏感性、稳健性、复现性。
- **07 Writing**：基于已验证证据形成论文，不自行发明核心数字。

## 5. Gate 原则

```text
Analysis Gate → Data Gate → Model Gate → Compute Gate → Verification Gate → Writing Gate → Final Gate
```
任何关键 Gate 未通过，不得把项目标记为完成。最终质量要求由 `08_verification/Final_Gate.md` 负责。

## 6. D/E 的定位

D/E 不是两条固定主流程，而是领域先验。首先判断 prediction、evaluation、optimization、classification、clustering、simulation、mechanism、network、risk、comprehensive_decision 等任务类型，再结合 D/E 先验缩小候选模型空间。禁止因为题目被标记为 D/E 就直接套模型清单。

## 7. 模型选择总原则

1. 先理解问题，再选模型；2. 优先可解释、可验证 baseline；3. 复杂模型必须有升级理由；4. 数据不足、约束冲突、泄漏或无法验证时不得强行使用复杂模型；5. 候选模型必须有选择依据；6. 核心模型必须说明适用条件、假设、变量、参数来源、求解和验证。

## 8. 可追溯与真实性

不得虚构数据、参数、实验结果、文献或竞赛结论；核心数字追溯到输入、Artifact 或 RunManifest；图表必须来自真实计算；不得把相关性写成因果关系；不得为了增加模型数量而堆叠无意义算法。

## 9. 工具调用原则

Stage Skill 判断能力需求 → 选择 Knowledge/Python/Visualization/Document Tool → 生成或更新 Artifact。新增 Python 模板必须有通用输入输出、适用问题、调用 Stage、验证方式及测试。

## 10. 历史题与 Benchmark

2024D/E、2025D/E 等用于能力缺口、benchmark、regression、泛化测试和案例知识提取，不得因单题方法而硬编码主流程。

## 11. Runtime 执行层

当前运行链为：

```text
External Host / CLI
 ↓ HostRequest
V0.7 Input Boundary
 ↓ Problem + Attachment Ingestion
Deterministic Ingestion Manifest + DataProfile
 ↓ RealLLMHostAdapter / ModelAdapter
RuntimeOrchestrator
 ↓
00-start → ProblemSpec → Gate
 ↓
01-analysis → ProblemMap → task_id Gate
 ↓
02-data → DataProfile → deterministic-facts Gate
 ↓
03-modeling → ModelPlan/ModelSpec/ModelComparison
 ↓
04-compute → ToolDispatchPlan
```

V0.7-B 规则：**LLM 负责语义提议，确定性摄取负责事实，Schema/Gate 负责最终接受。** DataProfile 的路径、大小、规模、schema、确定性质量检查不能由 LLM 覆写。

## 12. V0.8 自动模型选择

V0.8 已落地：

1. `tools/modeling/model_catalog.py`：封闭的可复用模型族目录；
2. `tools/modeling/model_selector.py`：按 ProblemMap task_id 分类任务，先硬约束淘汰，再按七维权重选择；
3. 七维权重：fit 25、data 15、constraints 15、interpretability 15、verifiability 15、robustness 10、cost 5；
4. `tools/modeling/model_plan_builder.py`：生成 ModelPlan 与逐任务 ModelSpec；
5. `tools/runtime/tool_dispatch.py`：将模型映射到封闭 Tool Registry 名称；
6. `artifacts/schemas/tool-dispatch.schema.json`：ToolDispatchPlan Schema；
7. `tools/runtime/real_host.py`：在 V0.7-B 三个 Artifact 后进入 03-modeling 与 04-compute dispatch planning；
8. `tests/modeling/test_model_selector.py`、`tests/runtime/test_v08_dispatch.py`：V0.8 离线契约测试。

V0.8 的选择分数**不是拟合性能指标**。真实误差、交叉验证、优化求解、仿真结果和 ResultBundle 留给 V0.9。LLM 可以解释和细化，但不能覆盖确定性选择结果，也不能任意发明工具名。

## 13. 当前实现状态

已建立 Master/Stage、Artifact Contract、JSON Schema、Gate、Traceability、Workflow Engine、E2E Demo、V0.6 Runtime、V0.6-C Real LLM Host、V0.7 真实题目/附件摄取、V0.7-B 结构化 Artifact，以及 **V0.8 自动模型选择 + ModelPlan/ModelSpec/ModelComparison + ToolDispatchPlan**。

当前环境未执行新增测试，因此不能声称测试已通过。下一阶段是 **V0.9：真正执行 ToolDispatch，生成 RunManifest/ResultBundle，并进入 Verification Gate。**
