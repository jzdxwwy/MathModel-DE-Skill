# V1.0-P：Claim Evidence Index + Deterministic Claim Binding

## 目标
P 不新增新的“答案 Gate”，而是把已有 PaperEvidence、ResultBundle、VerificationReport、UnifiedExecutionEvidence 的关系结构化，形成 Claim Evidence Index。

核心原则：
- 不让 LLM 猜测证据；
- 优先使用已有结构化 Artifact；
- 缺失关系则 FAIL_CLOSED；
- 不修改 Frozen ResultBundle；
- P 负责索引与绑定，不重算模型。

## 核心链
Claim
→ PaperEvidence
→ Result
→ Verification
→ UnifiedExecutionEvidence
→ Presentation

## Gate
新增 P 级 Claim Evidence Index Gate。
一个 Claim 至少需要：
1. claim_id；
2. statement；
3. Result ref；
4. Verification ref；
5. UnifiedExecutionEvidence ref。

缺任何一个 → FAIL。

## 与 O 的关系
O：验证 Claim lineage 和多来源 evidence 冲突。
P：把已有 Artifact 中的 Claim 关系确定性抽取成索引，减少手工填写。

## 安全边界
P 不进行模型重算、不修改结果、不选择冲突来源、不做隐式语义推断。

## 测试
本次实现后尚未运行 pytest。