# MathModel-DE-Skill Master Skill

> 面向 CUMCM D/E 题的可复用数学建模 Workflow Skill。

## 1. 核心定位
`题目/附件 → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Binding → Compute → ResultBundle → VerificationReport → PaperEvidence → 论文`

本 Skill 默认工作模式是 **Skill Development**；历史题用于能力缺口、Benchmark、Regression，不直接定义主流程。

## 2. 标准阶段
- 00 Start：摄取题目与附件 → ProblemSpec
- 01 Analysis：任务拆分 → ProblemMap
- 02 Data：数据体检与语义补充 → DataProfile
- 03 Modeling：确定性模型选择 → ModelPlan/ModelSpec/ModelComparison
- 04 Compute：Binding Gate → ToolDispatch → 数值执行 → RunManifest/ResultBundle
- 05 Visualization：真实结果 → 图表/PaperEvidence
- 06 Verification：公式、单位、可行性、误差、泄漏、敏感性、稳健性、复现性
- 07 Writing：只使用已验证证据写论文

## 3. D/E 定位
D/E 是先验，不是固定模板。先识别 prediction、evaluation、optimization、classification、clustering、simulation、mechanism、network、risk、comprehensive_decision 等任务类型，再结合 D/E 知识缩小模型空间。

## 4. Runtime / Gate
`Input Boundary → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Deterministic Binding → ToolDispatch → ToolRegistry → Numerical Adapter → ResultBundle → Verification`

Gate：`Analysis → Data → Model → Binding → Compute → Verification → Writing → Final`。任何关键 Gate 未通过不得标记完成。

## 5. V0.8
确定性模型选择器按七维评分选择模型：fit 25、data 15、constraints 15、interpretability 15、verifiability 15、robustness 10、cost 5。LLM 不能覆盖选择结果或任意发明工具。

## 6. V0.9-B
已建立显式 `data_binding`、统一 Template Adapter、ToolExecutionEngine 和正式 ResultBundle。缺少绑定或暂不支持时 `INPUT_BLOCKED`。

## 7. V0.9-C：数学输入契约与数值适配器
V0.9-C 把“Python 模板存在”推进为“数学输入可计算”：
- `time_series_baseline`：`data_path + time_col + target`
- `shortest_path`：`data_path + source + target`，边表 `u/v/weight`
- `mechanism_simulation`：事件流字段与时间间隔
- `optimization`：目标函数、变量、边界、可选约束
- `sensitivity`：目标函数、基准、扰动网格
- `monte_carlo`：事件表达式、变量、分布、样本量、seed

关键安全规则：LLM 只能提供结构化 binding，不能提交 Python；表达式执行使用白名单函数；缺少完整数学输入契约就阻断。

## 8. V0.9-D：确定性自动 Binding
V0.9-D 的核心不是“让 LLM 猜 binding”，而是建立：

`DataProfile → Binding Resolver → Binding Gate → ModelSpec/ToolDispatch → Compute`

### 8.1 Binding Resolver
`tools/modeling/data_binding.py` 只使用 DataProfile 的确定性事实和已验证的语义角色：
- 回归/分类：自动寻找唯一 tabular asset、唯一 `target/response/label/dependent` 角色，并从数值字段生成 predictors
- 时间序列：在回归绑定基础上要求唯一 `time/timestamp/datetime` 角色
- 网络：要求 `u/v/weight`，source/target 若不是数据事实则必须有结构化任务提示
- 优化/敏感性/Monte Carlo/机理模拟：如果无法从真实输入安全推导数学表达式或机理关系，必须 `BLOCKED`，不能猜

### 8.2 LLM 的新边界
LLM 可以提出 `target/features/source/target/time_col` 等**语义提示**，但 Resolver 必须逐项与 DataProfile 对照；不存在的路径、列或不满足契约的字段一律拒绝。LLM 不能覆盖确定性模型选择，也不能绕过 Binding Gate。

### 8.3 Blocked 是正常状态
`binding_status=BLOCKED` → ToolDispatch `BLOCKED` → Execution `INPUT_BLOCKED`。
这不是失败兜底，而是 Skill 的 fail-closed 设计：宁可停下来要求补充数学输入，也不生成伪结果。

## 9. 当前测试状态
已新增 V0.9-D binding resolver 测试文件，但当前环境没有执行 pytest；因此不得声称测试通过。GitHub 写入成功不等于运行时测试通过。

## 10. 下一阶段
V0.9-E 应继续把 Binding 结果与 **ResultBundle → VerificationReport** 接起来，并增加真实 D/E 历史附件的回归夹具：重点验证列绑定、时间字段、网络字段、数学表达式缺失时的阻断，以及同一输入重复运行时的可追溯性与确定性。
