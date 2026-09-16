# V0.9-E：结果验证与 Verification Gate

## 1. 目标
V0.9-E 把 V0.9-D 的“能够绑定并计算”推进为“计算结果必须经过独立验证才能进入后续论文流水线”。

主链：

`ResultBundle + RunManifest → Deterministic Verifier → VerificationReport → Verification Gate`

## 2. 验证原则

1. **证据优先**：只验证运行中真实产生的证据，不根据模型名称推断结果正确。
2. **缺证据不等于通过**：未运行的敏感性、稳健性等检查必须保持 `NOT_RUN`。
3. **失败闭环**：RunManifest 不是 `RUN_COMPLETE`、ResultBundle 缺失、数值非有限、模型不一致等情况不得通过。
4. **绑定一致性**：计算使用的 model_id 必须与 ToolDispatchPlan 一致。
5. **可追溯**：VerificationReport 保存 run_id、检查项、证据和 artifact_ref。
6. **不修改结果**：Verifier 只读计算结果，不重新拟合、不修正数值、不替模型做解释。

## 3. 当前自动检查

- RunManifest / ResultBundle 是否完整
- ResultBundle 是否 `VALIDATED`
- outputs / metrics 是否存在 NaN / Inf
- dispatch model 与 result model 是否一致
- binding 是否被 BLOCKED
- sensitivity / robustness 是否有真实证据；没有则 `NOT_RUN`

## 4. Gate

- 全部 PASS → `PASS`
- 无 FAIL，但存在 WARN/NOT_RUN → `PASS_WITH_WARNINGS`
- 存在 FAIL → `FAIL`

任何 `FAIL` 都会阻止 RealLLMHost 将本次任务标记为成功。

## 5. 当前边界

V0.9-E 还不是领域级验证器。单位一致性、约束可行性、交叉验证、残差诊断、参数敏感性、随机重复实验等需要结合具体模型注册验证规则。

因此下一阶段应建设 **V0.9-F Domain Verification Rules**：把不同模型族的可验证条件注册成规则，而不是继续在通用 Verifier 中堆叠特例。
