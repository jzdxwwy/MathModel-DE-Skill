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
- 06 Verification：通用核验 + Domain Rule Registry + Mathematical Acceptance → VerificationReport → Verification Gate
- 07 Writing：只使用已验证证据写论文

## 3. D/E 定位
D/E 是先验，不是固定模板。先识别 prediction、evaluation、optimization、classification、clustering、simulation、mechanism、network、risk、comprehensive_decision 等任务类型，再结合 D/E 知识缩小模型空间。

## 4. Runtime / Gate
`Input Boundary → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Deterministic Binding → ToolDispatch → ToolRegistry → Numerical Adapter → ResultBundle → Domain Rule Registry → Mathematical Acceptance → VerificationReport`

Gate：`Analysis → Data → Model → Binding → Compute → Verification → Writing → Final`。任何关键 Gate 未通过不得标记完成。

## 5. V0.8
确定性模型选择器按七维评分选择模型：fit 25、data 15、constraints 15、interpretability 15、verifiability 15、robustness 10、cost 5。LLM 不能覆盖选择结果或任意发明工具。

## 6. V0.9-B
已建立显式 `data_binding`、统一 Template Adapter、ToolExecutionEngine 和正式 ResultBundle。缺少绑定或暂不支持时 `INPUT_BLOCKED`。

## 7. V0.9-C：数学输入契约与数值适配器
V0.9-C 把“Python 模板存在”推进为“数学输入可计算”：时间序列、最短路径、事件流/轨迹、显式优化、敏感性、Monte Carlo 均有受控适配器。

关键安全规则：LLM 只能提供结构化 binding，不能提交 Python；表达式执行使用白名单函数；缺少完整数学输入契约就阻断。

## 8. V0.9-D：确定性自动 Binding
核心链：`DataProfile → Binding Resolver → Binding Gate → ModelSpec/ToolDispatch → Compute`。

Binding Resolver 只使用 DataProfile 的确定性事实和已验证语义角色；回归/分类/时间序列/网络可以在满足唯一性和字段契约时自动绑定。优化、敏感性、Monte Carlo、机理模拟无法安全推导数学表达式时必须 `BLOCKED`，不能猜。

LLM 可以提出语义提示，但不能覆盖确定性模型选择，也不能绕过 Binding Gate。`BLOCKED → INPUT_BLOCKED` 是正常的 fail-closed 状态。

## 9. V0.9-E：ResultBundle → VerificationReport
V0.9-E 建立通用结果验证器与执行桥，检查运行完整性、ResultBundle 状态、有限数值、模型一致性、Binding 状态及证据缺失。

## 10. V0.9-F：Domain Verification Rules
V0.9-F 新增 `tools/verification/domain_verifier.py`，并将其接入 `result_verifier.py`。验证按模型族读取真实证据：

- 回归：R²、MAE、RMSE、可复现性证据
- 分类：Accuracy、F1
- 时间序列：时序误差指标、预测步长绑定
- 优化：约束可行性证据
- 最短路径：路径与距离输出
- Monte Carlo / 敏感性：重复次数、置信区间等证据
- 机理/轨迹：输出存在性及稳定性附加验证

规则采用 **evidence-first**：缺少指标或证据只能得到 `NOT_RUN`，不能被模型名称或经验自动补成 PASS。

## 11. V0.9-G：Domain Verification Rule Registry
V0.9-G 将领域验证从条件分支升级为注册式架构：

`ResultBundle → Generic Verification → Rule Registry → Domain Rule Set → VerificationReport → Gate`

新增：
- `tools/verification/rule_registry.py`：规则集注册、模型族索引、规则解析与执行
- `tools/verification/default_rules.py`：默认模型族规则注册表
- `00_governance/V0_9_G_RULE_REGISTRY.md`：Registry 契约与扩展规范

当前规则集：regression-v1、classification-v1、time-series-v1、optimization-v1、network-v1、stochastic-v1、mechanism-v1。

规则注册具有唯一性约束：同一 model family 不允许绑定多个规则集。未注册模型保持 `NOT_RUN`，不得假定通过。Rule Registry 不修改 ResultBundle，只负责选择和执行确定性验证规则。

## 12. V0.9-H：Schema-driven Mathematical Acceptance
V0.9-H 将验证从“证据存在性”推进到“数学验收”。核心链：

`ModelSpec + DataProfile + ResultBundle + Rule Registry → Acceptance Rules → Rule Evaluator → VerificationReport → Gate`

新增：
- `artifacts/schemas/verification-rule.schema.json`：验收规则结构契约
- `tools/verification/rule_evaluator.py`：数学不变量、数值范围和证据绑定验收器
- `00_governance/V0_9_H_MATHEMATICAL_ACCEPTANCE.md`：V0.9-H 治理规范

当前验收重点：
- 回归：指标有限性、R² 范围、CV/验证绑定、数据泄漏检查绑定
- 分类：Accuracy/F1 有限性与范围、CV、类别分布证据
- 时间序列：时间顺序切分、未来信息泄漏、预测步长
- 优化：约束可行性、目标函数有限性、约束定义、最优性证据
- 网络：路径、距离、边合法性、权重一致性证据
- 随机模型：重复次数、置信区间、随机种子

验收语义仍保持 fail-closed：明确违反数学不变量 → `FAIL`；缺少足够证据 → `NOT_RUN`；证据充分且满足规则 → `PASS`。

V0.9-H 不是符号定理证明器，不会把缺失证据自动推断为正确；其目标是建立可扩展的数学验收层。

## 13. 当前测试状态
V0.9-H 代码与治理文件已写入 GitHub，但当前环境没有实际执行 pytest，因此不能声称测试通过。GitHub commit 成功不等于运行时验证通过。

## 14. 下一阶段
V0.9-I：从“绑定/结果中的验收证据”进一步走向 **Evidence Materialization + Independent Recompute**，在安全范围内直接从 ResultBundle 和数据产物独立复算指标、约束、路径、统计量，并建立历史题回归测试夹具与证据血缘。
