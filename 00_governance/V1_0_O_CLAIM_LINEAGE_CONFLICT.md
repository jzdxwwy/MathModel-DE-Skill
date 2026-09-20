# V1.0-O：Claim-Level Lineage + Evidence Conflict Closure

## 目标

O 不再只证明“存在一个统一执行证据”，而是把论文中的每一个可验证 Claim 提升为显式证据图节点，并对同一 Claim 的多来源观测执行确定性冲突检测。

## 核心链

Claim → PaperEvidence → Result → Verification / Presentation → UnifiedExecutionEvidence → Input

## 规则

1. Claim 必须有唯一 claim_id 和非空 statement。
2. Result、Verification、Figure/Table/Equation 的引用必须显式记录，不靠字符串搜索猜测。
3. 每个可验证 Claim 必须引用 UnifiedExecutionEvidence；G/H/K 原始 evidence 只能作为 source_evidence 保留。
4. 多来源数值观测只有在 unit 相同、comparison_type=numeric 且声明 atol/rtol 后才可比较。
5. 单位不同、类型不同或 comparison_type=none 时，不进行隐式换算或语义解释；不可比较状态阻止 PASS。
6. exact 比较只比较声明的 normalized_value/value，不进行自然语言语义推断。
7. 数值冲突必须 FAIL_CLOSED；不得选择一个“更可信”的来源。
8. Frozen ResultBundle 不得因冲突而修改。
9. 缺少 Claim lineage、UnifiedExecutionEvidence 或可比较 observation 时，不得伪装成“无冲突”。
10. O 是结构化 Gate，不用 serialized text 搜索替代字段级校验。

## Gate

- Claim Lineage Gate：缺 canonical UE、断边、空 Claim → FAIL；没有 lineage artifact 且无法构建 → NOT_RUN。
- Evidence Conflict Gate：冲突、不可比较、缺 observation → FAIL；无冲突 → PASS。
- Final Submission Gate 增加 F17 CLAIM_LINEAGE_CONFLICT，只有两部分都 PASS 时 F17 才 PASS。

## 不做什么

O 不判断哪个来源更正确，不做人工仲裁，不做隐式单位换算，不重算模型。它只验证声明的 lineage、来源闭合与确定性可比性。

## 与 N 的关系

N 解决“出版物只引用 UnifiedExecutionEvidence”；O 进一步解决“同一个 Claim 内部的来源是否一致，以及 Claim 是否能沿显式图回溯到执行证据”。

## 测试

已加入 tests/verification/test_v10_o_claim_lineage.py。当前会话没有实际运行 pytest，因此不能声称测试通过。
