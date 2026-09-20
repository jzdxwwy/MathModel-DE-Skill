# V1.0-R：Claim 数值级自动溯源

## 目标
R 将 Q 的实体闭环进一步推进到“论文 Claim 中的具体数值必须与 ResultBundle 中的真实数值一致”。

核心链：
Claim observation
→ ClaimEvidenceIndex result ref
→ ResultBundle value
→ 数值比较
→ Claim Numeric Trace

## 规则
- 只读取结构化 observations，不解析 statement 自然语言。
- 支持 output:<name>、metric:<name>。
- 默认 atol=1e-8、rtol=1e-6，并明确记录在 Trace 中。
- 单位若同时存在则必须精确一致；不做隐式单位换算。
- 缺失、非数值、无法解析、超容差均 FAIL_CLOSED。
- 不修改 ResultBundle，不重算模型，不选择冲突来源。

## 与 Q 的关系
Q：证明“这个 Claim 引用的实体存在并闭合到执行”。
R：证明“这个 Claim 声称的具体数值与实体中的真实数值一致”。

## 安全边界
R 不从 Claim statement 猜数字；论文作者/写作层必须显式生成 observations。

## 测试
新增 R 单元测试；尚未实际运行 pytest，不能宣称测试通过。
