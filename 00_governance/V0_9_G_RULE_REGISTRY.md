# V0.9-G：Domain Verification Rule Registry

## 1. 目标

V0.9-F 已经能够针对模型族生成领域检查，但规则仍集中在单一实现中。V0.9-G 将其升级为 **Rule Registry**：模型族与验证规则集通过注册表关联，Verification Engine 不再依赖大量 `if/elif` 分支。

主链：

`ResultBundle → Generic Verification → Rule Registry → Domain Rule Set → VerificationReport → Gate`

## 2. Registry 契约

每个规则集包含：

- `rule_id`：稳定标识
- `model_ids`：适用模型族
- `version`：规则版本
- `handler`：确定性验证函数

同一个 model family 不允许注册多个规则集，避免验证语义冲突。

## 3. 当前默认规则集

| Rule Set | Model Family |
|---|---|
| regression-v1 | linear_regression, tree_ensemble_regression |
| classification-v1 | logistic_classification, tree_ensemble_classification |
| time-series-v1 | time_series_baseline |
| optimization-v1 | optimization |
| network-v1 | shortest_path |
| stochastic-v1 | monte_carlo, sensitivity |
| mechanism-v1 | mechanism_simulation, trajectory_reconstruction |

## 4. Fail-closed

未注册模型不会被假定为“通过”，而是产生 `NOT_RUN` 检查 `V-G99`。

领域规则只能增加验证证据，不能修改 ResultBundle，也不能替模型重新计算结果。

## 5. 后续扩展

V0.9-H 应继续把规则从“存在某指标”升级为真正的数学验收条件，例如：

- 回归：残差诊断、交叉验证、数据泄漏
- 分类：类别不平衡、混淆矩阵、交叉验证
- 时间序列：滚动验证、时间泄漏、预测窗口
- 优化：约束逐项可行性、边界解、最优性证据
- 网络：边合法性、连通性、路径权重一致性
- 随机模拟：重复次数、随机种子、置信区间、稳定性
- 全模型：单位/量纲、输入输出追踪、图表与结果一致性

V0.9-G 的重点是建立可扩展的验证基础设施，而不是一次性覆盖所有数学正确性。
