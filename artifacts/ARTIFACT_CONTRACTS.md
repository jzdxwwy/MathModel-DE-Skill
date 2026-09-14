# Artifact Contracts v2

> 版本：0.1
> 
> 目标：定义数学建模工作流阶段之间传递的结构化中间产物。

## 1. 为什么需要 Artifact Contract

传统流程容易形成：

```text
Markdown → Agent记忆 → Python → Markdown
```

这种方式的问题是阶段之间边界模糊，容易出现：

- 前一阶段没有完成，后一阶段已经开始；
- 模型选择与实际数据脱节；
- 代码使用了未确认的字段或参数；
- 论文出现无法追溯的数字；
- 修改前序结论后，下游结果没有同步更新。

v2 改为：

```text
Stage → Artifact → Gate → Stage
```

## 2. 核心 Artifact

### 2.1 ProblemSpec

描述原始问题，不加入未经确认的建模结论。

最少包含：

- problem_id
- source_files
- background
- questions
- explicit_requirements
- known_data
- unknowns
- mode

### 2.2 ProblemMap

把题目转化为可建模的问题结构。

最少包含：

- question_id
- task_type
- decision_variables
- response_variables
- inputs
- constraints
- assumptions
- dependencies
- candidate_method_families

`task_type` 使用通用任务分类，例如：

- prediction
- evaluation
- optimization
- classification
- clustering
- simulation
- mechanism
- network
- risk
- comprehensive_decision

D/E 标签属于先验字段，不替代 task_type。

### 2.3 DataProfile

描述附件和数据是否适合进入建模。

最少包含：

- file_id
- table/schema
- row_count
- column_profile
- missingness
- duplicates
- outliers
- units
- time_granularity
- entity_keys
- data_quality_issues
- recommended_preprocessing

### 2.4 ModelPlan

描述候选模型与选择逻辑，不直接等同于代码。

最少包含：

- question_id
- candidate_models
- baseline_model
- comparison_criteria
- selected_model
- upgrade_reason
- assumptions
- validation_plan

### 2.5 ModelSpec

描述准备实际求解的模型。

最少包含：

- model_id
- variables
- parameters
- objective
- equations_or_rules
- constraints
- parameter_sources
- solution_method
- stopping_rules
- expected_outputs
- limitations

### 2.6 RunManifest

记录一次可复现计算运行。现有 `schemas/run-manifest.schema.json` 继续作为基础。

必须能够回答：

> 用什么输入、什么代码、什么参数、什么环境、什么随机种子，得到什么输出？

### 2.7 ResultBundle

记录实际计算结果。

最少包含：

- run_id
- question_id
- result_tables
- key_numbers
- metrics
- figures
- output_files
- warnings
- provenance

核心数字必须能够追溯到 RunManifest 和实际输出文件。

### 2.8 VerificationReport

记录验证结果。

最少包含：

- question_id
- checks
- numerical_validation
- boundary_checks
- feasibility_checks
- residual_or_error_checks
- sensitivity
- robustness
- reproducibility
- unresolved_issues
- verdict

`verdict` 至少包括：`PASS / CONDITIONAL / FAIL`。

### 2.9 PaperEvidence

提供给论文写作阶段的“已验证证据包”。

最少包含：

- question_id
- conclusion
- supporting_numbers
- supporting_figures
- model_reference
- verification_reference
- limitations
- source_run_ids

Writing Stage 优先消费 PaperEvidence，而不是直接消费任意 Python 输出。

## 3. Artifact 生命周期

每个核心 Artifact 应具有：

```text
DRAFT
  ↓
VALIDATED
  ↓
FROZEN
  ↓
SUPERSEDED
```

- `DRAFT`：阶段正在形成；
- `VALIDATED`：通过本阶段 Gate；
- `FROZEN`：已经被下游正式消费；
- `SUPERSEDED`：前序版本已被新版本替代。

禁止静默修改已经 FROZEN 的核心 Artifact。

## 4. 来源追踪

Artifact 中的核心事实应至少指向以下一种来源：

- source_file / source_location
- upstream_artifact
- run_id
- code/output file

禁止出现“来源不明但看起来合理”的核心数字。

## 5. 版本关系

Artifact 之间必须能够形成：

```text
ProblemSpec
   ↓
ProblemMap v1
   ↓
DataProfile v1
   ↓
ModelPlan v1
   ↓
ModelSpec v1
   ↓
RunManifest r001
   ↓
ResultBundle r001
   ↓
VerificationReport r001
   ↓
PaperEvidence r001
```

如果 ModelSpec 修改，应允许重新计算并形成新的 RunManifest/ResultBundle，而不是覆盖旧结果。

## 6. 第一阶段实现范围

v0.1 不要求立即为所有 Artifact 实现完整 JSON Schema。

优先顺序：

1. ProblemSpec
2. ProblemMap
3. DataProfile
4. ModelPlan
5. ModelSpec
6. ResultBundle
7. VerificationReport
8. PaperEvidence

现有 RunManifest 与 Frozen Numbers Schema 继续保留，并逐步纳入统一 Artifact 体系。
