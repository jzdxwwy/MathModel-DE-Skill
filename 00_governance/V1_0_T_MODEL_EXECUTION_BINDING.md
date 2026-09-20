# V1.0-T：模型—执行绑定

## 目标
将 ModelSpec 的身份与实际执行产物绑定：

ModelSpec → ResultBundle → UnifiedExecutionEvidence

## 确定性规则
- ResultBundle.model_id 必须等于 ModelSpec.model_id；
- ResultBundle.run_id 必须与 UnifiedExecutionEvidence.run_id 一致；
- UE.result_bundle_hash 必须等于当前 ResultBundle 的实际 SHA256；
- UE.execution_status 必须为 SUCCESS；
- ModelSpec、ResultBundle、UE 三者均必须存在；
- 记录 ModelSpec SHA256、ResultBundle SHA256、equation_refs、parameter_symbols。

## 重要边界
T 首版证明的是“模型身份与执行产物绑定”，不是证明执行代码内部进行了完整公式级重算。
因此不声称完成代码级公式等价验证。

## 与 S 的关系
S：Claim → ModelSpec equation / parameter。
T：ModelSpec → ResultBundle → UnifiedExecutionEvidence。
二者组合后形成 Claim → ModelSpec → Execution → Result 的闭环。

## 测试
已加入单元测试，但尚未实际运行 pytest。
