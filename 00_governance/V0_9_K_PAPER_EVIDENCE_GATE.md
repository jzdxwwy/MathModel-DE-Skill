# V0.9-K PaperEvidence First-Class Artifact + Evidence Lineage Gate

## 1. Goal

把 PaperEvidence 从写作阶段的普通中间对象升级为一等 Artifact，并建立强制 Evidence Lineage Gate。

核心原则：

> 论文中的关键数字、表格、图和结论，必须能够追溯到 VerificationReport、ResultBundle 以及上游输入/数据证据。

## 2. Pipeline

`ResultBundle → VerificationReport → EvidenceLineage → PaperEvidence → PaperEvidence Gate → Writing`

## 3. PaperEvidence contract

每个 material claim 必须显式提供：

- `evidence_refs`
- `verification_refs`
- `result_refs`
- `lineage_refs`

不得仅使用自然语言描述“来源”。

## 4. Gate rules

V-K01：VerificationReport 必须为 `PASS`。

V-K02：ResultBundle 必须为 `VALIDATED` 或 `FROZEN`。

V-K03：EvidenceLineage 必须至少包含 input/data、run、result、verification 节点。

V-K04：PaperEvidence 至少包含一个 claim。

V-K05：每个 claim 必须同时具有 verification_refs、result_refs 和能够在 EvidenceLineage 中解析的 lineage_refs。

任何一项失败 → `FAIL`；不允许降级为 PASS_WITH_WARNINGS。

## 5. Freeze rule

只有 Gate=`PASS` 时，PaperEvidence 才可以标记为 `FROZEN` 并进入论文写作流水线。

## 6. Scope boundary

V0.9-K 解决“论文证据能否追溯”的问题，不负责判断论文语言是否优秀，也不替代数学验收、独立复算或最终格式审查。

## 7. Next

V0.9-L：将 PaperEvidence Gate 接入完整 Writing Pipeline，并建立 Figure/Table/EQUATION evidence binding，最终形成 `PaperEvidence → Paper Draft → Final Submission Gate` 的闭环。
