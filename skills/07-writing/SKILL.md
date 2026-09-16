# Stage 07 — Writing Skill

## 目的
把已经验证的结果转化为可追溯的论文证据和论文文本。

## 输入
- `ModelSpec`
- `ResultBundle`
- `VerificationReport`
- `EvidenceLineage`
- `PaperEvidence`

## 核心规则
- 不自行创造核心数字；
- 重要结论必须关联模型、结果和验证依据；
- 每个 material claim 必须显式提供 `verification_refs`、`result_refs`、`lineage_refs`；
- 图表必须来自真实结果，并在后续阶段绑定相应证据；
- 优点、缺点、假设和局限必须与实际模型一致；
- 未通过 Verification Gate 的结果不得进入最终 PaperEvidence；
- 未通过 PaperEvidence Gate 的 claim 不得标记为最终论文证据。

## 输出
- `PaperEvidence`
- PaperEvidence Gate Report
- 论文草稿/章节素材

## Gate
`Verification PASS → PaperEvidence Gate PASS → PaperEvidence FROZEN → Writing`

任何关键数字、表格、图或结论缺少可追溯证据时，必须阻断，而不是由语言模型补写来源。
