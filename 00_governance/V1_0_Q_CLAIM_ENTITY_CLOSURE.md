# V1.0-Q：Claim → Entity → Verification → Execution Closure

## 目标
Q 将 P 的“引用存在”升级为“引用对象真实存在且属于本次计算链”。

核心链：
Claim
→ Result Entity
→ Verification Entity
→ ResultBundle
→ UnifiedExecutionEvidence

## Q 的确定性解析规则
### Result
支持：
- `output:<name>`：ResultBundle.outputs 中唯一同名 output；
- `metric:<name>`：ResultBundle.metrics 中存在该 metric；
- `artifact:<path>`：ResultBundle.artifacts 中唯一同路径 artifact；
- `result-bundle.json` 或其路径：绑定整个 ResultBundle；
- 裸 output name：仅在 ResultBundle.outputs 中唯一时解析。
无法唯一解析 → FAIL_CLOSED。

### Verification
支持：
- `check:<check_id>`：VerificationReport.checks 中唯一匹配且 status=PASS；
- 裸 check_id：同上；
- `verification-report.json`：仅作为报告级绑定，必须由报告 gate_decision 支持。

### Execution
Q 要求：
- UnifiedExecutionEvidence 存在且 execution_status=SUCCESS；
- UE.run_id == ResultBundle.run_id；
- UE.result_bundle_hash == 实际 ResultBundle SHA256；
- Claim 的 UE ref 必须指向 canonical UnifiedExecutionEvidence。

## 安全边界
- 不读取 Claim 自然语言去猜结果；
- 不做隐式单位换算；
- 不选择多个冲突 Result；
- 不重算模型；
- 不修改 Frozen ResultBundle；
- 无法解析、缺失、冲突均 FAIL_CLOSED。

## 与 P/O 的关系
P：确定性建立 Claim 引用索引；
O：检测证据冲突；
Q：验证引用对象实体级真实存在并闭合到执行证据。

## 测试
本版本增加 Q 单元测试；当前仓库未在实现环境中实际运行 pytest，故不能宣称测试已通过。
