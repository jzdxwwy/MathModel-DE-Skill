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
- 06 Verification：ResultBundle 独立核验 → VerificationReport → Verification Gate
- 07 Writing：只使用已验证证据写论文

## 3. D/E 定位
D/E 是先验，不是固定模板。先识别 prediction、evaluation、optimization、classification、clustering、simulation、mechanism、network、risk、comprehensive_decision 等任务类型，再结合 D/E 知识缩小模型空间。

## 4. Runtime / Gate
`Input Boundary → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Deterministic Binding → ToolDispatch → ToolRegistry → Numerical Adapter → ResultBundle → VerificationReport`

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
V0.9-E 新增确定性结果验证器 `tools/verification/result_verifier.py` 与执行桥 `tools/runtime/verification_engine.py`。

### 自动验证内容
- RunManifest 与 ResultBundle 是否完整
- ResultBundle 是否为 `VALIDATED`
- 输出和指标是否出现 NaN/Inf
- Dispatch 的 `model_id` 与 ResultBundle 是否一致
- Binding 是否被阻断
- 敏感性、稳健性是否具有真实证据；没有证据必须保持 `NOT_RUN`

### Verification Gate
- 全部 PASS → `PASS`
- 无 FAIL，但存在 WARN/NOT_RUN → `PASS_WITH_WARNINGS`
- 存在 FAIL → `FAIL`

任何 `FAIL` 都不能进入后续“已验证结果”状态。Verifier 不修改计算结果，不根据模型名称推断正确性。

## 10. 当前测试状态
V0.9-E 代码与治理文件已写入 GitHub，但当前环境没有实际执行 pytest，因此不能声称测试通过。GitHub commit 成功不等于运行时验证通过。

## 11. 下一阶段
V0.9-F：建立 **Domain Verification Rules**。把回归、分类、时间序列、优化、网络、随机模拟等模型族的单位、约束、残差、交叉验证、敏感性、稳健性、复现性检查注册为规则，使 Verification 从通用 sanity check 升级为数学模型级验收。
