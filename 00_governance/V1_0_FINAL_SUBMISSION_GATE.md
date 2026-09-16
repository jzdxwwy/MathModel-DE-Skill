# V1.0 — Final Submission Gate

## 1. 定位

V1.0 是 MathModel-DE-Skill 从“可验证建模流水线”进入“可发布交付流水线”的总门禁。

目标不是重新计算模型，而是汇总已经存在的证据、验证、展示物化和交付文件，并以 fail-closed 方式决定是否允许标记为最终提交。

## 2. 最终链

`Problem → Data → Model → Compute → Verification → PaperEvidence → PresentationEvidence → RenderedConsistency → Materialization → RenderManifest → PaperManifest → SubmissionManifest → Final Submission Gate`

## 3. Gate 原则

1. `PASS` 只能来自真实、已持久化的证据。
2. `NOT_RUN` 不得自动升级为 `PASS`。
3. 缺失的强制交付物直接 `FAIL`。
4. ResultBundle 是权威计算结果；Final Gate 不修改它。
5. SubmissionManifest 是可复现交付索引；Final Gate 不伪造 artifact hash。
6. 最终 Gate 不负责替模型重新计算，也不替代 Domain Verification。

## 4. V1.0 首版检查项

### F1 ResultBundle
必须存在，且状态为 `VALIDATED` 或 `FROZEN`。

### F2 VerificationReport
必须有明确 gate decision。`FAIL` 阻断；缺失或 `NOT_RUN` 不得宣称最终通过。

### F3 PresentationRenderManifest
如果本次提交包含展示物，则其 materialization/render gate 必须通过。

### F4 SubmissionManifest
V1.0 默认要求存在，用于记录 run、输入 hash、环境和交付 artifact hash。

### F5 Paper Deliverable
当调用方要求论文交付时，必须存在 PDF/DOCX 等指定论文文件。

### Additional Artifact Checks
调用方可以显式声明 `required_artifacts`。任何声明的文件不存在均为 `FAIL`。

## 5. Gate 决策

- 任一 `FAIL` → `FAIL`
- 无 `FAIL`，但存在 `NOT_RUN` → `NOT_RUN`
- 全部检查 `PASS` → `PASS`

因此最终状态只有在所有必要检查真实通过后才可能是 `PASS`。

## 6. 当前实现边界

V1.0 首版已经实现确定性的证据聚合和交付存在性检查，但尚未实现：

- PDF/Word 像素级视觉检查；
- OCR 全文数字复核；
- 完整公式符号等价证明；
- Word/PDF 排版质量评分；
- ZIP 内部递归完整性审计；
- 从零重新执行全部代码的独立重建。

这些属于 V1.0 后续增强，而不是通过“默认 PASS”掩盖。

## 7. 红线

以下任何情况禁止最终标记 PASS：

- 核心 ResultBundle 不存在或未验证；
- Verification Gate 未通过；
- 必要 presentation materialization 未通过；
- SubmissionManifest 缺失；
- 显式要求的论文/结果/代码文件缺失；
- 任何关键检查仍为 `NOT_RUN`。

## 8. 输出

运行级报告：

`runs/<run_id>/final-submission-gate.json`

报告至少包含：

- run_id
- checks
- blocking_failures
- not_run_checks
- gate_decision
- required artifact hashes

V1.0 的 PASS 意味着“当前定义的 Final Submission Gate 已通过”，不意味着系统已经证明数学模型绝对正确；数学正确性仍由前置 Verification / Independent Recompute / Domain Rules 负责。
