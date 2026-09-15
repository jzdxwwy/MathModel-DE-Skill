# MathModel-DE-Skill Master Skill

> 面向 CUMCM D/E 题的可复用数学建模 Workflow Skill。

## 1. 核心定位
`题目/附件 → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Compute → ResultBundle → VerificationReport → PaperEvidence → 论文`

本 Skill 默认工作模式是 **Skill Development**；历史题用于能力缺口、Benchmark、Regression，不直接定义主流程。

## 2. 标准阶段
- 00 Start：摄取题目与附件 → ProblemSpec
- 01 Analysis：任务拆分 → ProblemMap
- 02 Data：数据体检与语义补充 → DataProfile
- 03 Modeling：确定性模型选择 → ModelPlan/ModelSpec/ModelComparison
- 04 Compute：ToolDispatch → 数值执行 → RunManifest/ResultBundle
- 05 Visualization：真实结果 → 图表/PaperEvidence
- 06 Verification：公式、单位、可行性、误差、泄漏、敏感性、稳健性、复现性
- 07 Writing：只使用已验证证据写论文

## 3. D/E 定位
D/E 是先验，不是固定模板。先识别 prediction、evaluation、optimization、classification、clustering、simulation、mechanism、network、risk、comprehensive_decision 等任务类型，再结合 D/E 知识缩小模型空间。

## 4. Runtime / Gate
`Input Boundary → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → ToolDispatch → ToolRegistry → Numerical Adapter → ResultBundle → Verification`

Gate：`Analysis → Data → Model → Binding → Compute → Verification → Writing → Final`。任何关键 Gate 未通过不得标记完成。

## 5. V0.8
确定性模型选择器按七维评分选择模型：fit 25、data 15、constraints 15、interpretability 15、verifiability 15、robustness 10、cost 5。LLM 不能覆盖选择结果或任意发明工具。

## 6. V0.9-B
已建立显式 `data_binding`、统一 Template Adapter、ToolExecutionEngine 和正式 ResultBundle。当前真实接通线性回归、树模型比较、逻辑回归分类；缺少绑定或暂不支持时 `INPUT_BLOCKED`。

## 7. V0.9-C：数学输入契约与数值适配器
V0.9-C 把“Python 模板存在”推进为“数学输入可计算”：

### 已建立的数学输入契约
- `time_series_baseline`：`data_path + time_col + target`，可选 features / horizon / min_train / seed
- `shortest_path`：`data_path + source + target`，可选 directed；边表必须有 `u/v/weight`
- `mechanism_simulation`：`data_path + entity_col + time_col + node_col`，可选最大时间间隔
- `optimization`：`objective_expression + variables + bounds`，可选约束与初值
- `sensitivity`：`objective_expression + base + grid`
- `monte_carlo`：`event_expression + variables + distributions + n + seed`

### 已接入 Tool Registry
- 时间序列 rolling-origin Ridge
- Dijkstra 最短路径
- 事件流/轨迹重构
- 显式数学表达式优化 SLSQP
- 显式数学表达式 OAT 敏感性分析
- 显式数学表达式 Monte Carlo

### 关键安全规则
LLM 只能提供结构化 binding，不能提交 Python。数学表达式仅允许声明变量和白名单函数；禁止 import、lambda、语句和任意代码。没有完整数学输入契约就 `INPUT_BLOCKED`。

## 8. 当前测试状态
已新增 V0.9-C 数学输入契约测试，但当前环境未实际运行 pytest，因此不得声称测试通过。

## 9. 下一阶段
V0.9-D 应把 **ModelSpec → 自动 binding 生成 → DataProfile 对照 → Binding Gate → Compute** 完整闭环，并建立 D/E 历史题回归夹具，验证同一 Skill 能否从真实附件自动得到可执行输入，而不是要求用户手工填写 binding。
