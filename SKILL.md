# MathModel-DE-Skill Master Skill

> 面向 CUMCM D/E 题的可复用数学建模 Workflow Skill。

## 1. 核心定位
`题目/附件 → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Binding → Compute → ResultBundle → VerificationReport → PaperEvidence → 论文`

本 Skill 默认工作模式是 **Skill Development**；历史题用于能力缺口、Benchmark、Regression，不直接定义主流程。

## 2. 标准阶段
- 00 Start：摄取题目与附件 → ProblemSpec
- 01 Analysis：任务拆分 → ProblemMap
- 02 Data：数据体检与语义补充 → DataProfile
- 03 Modeling：确定性模型选择 → ModelPlan/ModelSpec/ModelComparison
- 04 Compute：Binding Gate → ToolDispatch → 数值执行 → RunManifest/ResultBundle
- 05 Visualization：真实结果 → Figure/Table/Equation Evidence Binding → Presentation Data Manifest → Materialization → Render Manifest → PaperEvidence
- 06 Verification：通用核验 + Domain Rule Registry + Mathematical Acceptance + Independent Recompute + Evidence Lineage + Rendered Consistency + Presentation Materialization + Reproducibility Manifest → VerificationReport
- 07 Writing：PaperEvidence Gate 与 Presentation Gate 通过后才允许冻结证据并写论文；PaperManifest 规定论文结构与证据映射
- 08 Final Submission：Final Submission Gate 汇总验证、展示物化、论文与交付文件，决定最终是否允许标记提交完成

## 3. D/E 定位
D/E 是先验，不是固定模板。先识别 prediction、evaluation、optimization、classification、clustering、simulation、mechanism、network、risk、comprehensive_decision 等任务类型，再结合 D/E 知识缩小模型空间。

## 4. Runtime / Gate
`Input Boundary → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Deterministic Binding → ToolDispatch → ToolRegistry → Numerical Adapter → ResultBundle → Domain Rule Registry → Mathematical Acceptance → Independent Recompute → Evidence Lineage → PaperEvidence → Presentation Evidence → Rendered Consistency → Presentation Materialization → Render Manifest → PaperManifest → SubmissionManifest → Cross-Artifact Consistency → Writing → Final Submission Gate`

Gate：`Analysis → Data → Model → Binding → Compute → Verification → PaperEvidence → Presentation → RenderedConsistency → Materialization → Reproducibility → CrossArtifactConsistency → Writing → FinalSubmission`。任何关键 Gate 未通过不得标记完成。

## 5–19. 已有版本
V0.8–V1.0 首版能力保持不变，具体实现与治理文件见仓库对应版本文档。

## 20. V1.0-B：Cross-Artifact Consistency Gate
V1.0-B 解决“每个 Artifact 单独合法，但彼此引用错位”的问题。

核心链：
`PaperManifest → PaperEvidence → PresentationDataManifest → ResultBundle → VerificationReport`
并同时检查：
`PresentationDataManifest → RenderManifest → SubmissionManifest → 实际交付文件`

新增：
- `tools/verification/cross_artifact_consistency.py`
- `artifacts/schemas/cross-artifact-consistency.schema.json`
- `tests/verification/test_v10_cross_artifact.py`
- `00_governance/V1_0_B_CROSS_ARTIFACT_CONSISTENCY.md`

当前 B01–B08 检查：
- PaperManifest 的 claim_refs 是否全部解析到 PaperEvidence；
- PaperEvidence 的 material claims 是否都进入 PaperManifest；
- figure/table/equation 引用是否解析到 PresentationDataManifest；
- PresentationDataManifest 是否绑定到 VALIDATED/FROZEN ResultBundle；
- Presentation evidence 是否闭合到 RenderManifest；
- SubmissionManifest 中的 artifact 路径与 SHA256 是否和实际文件一致；
- run_id 是否跨运行 Artifact 一致。

V1.0 Final Submission Gate 已新增 `F6_CROSS_ARTIFACT`，默认调用 V1.0-B。任一跨 Artifact 闭环失败即阻断最终 PASS。

V1.0-B 仍不做 PDF/Word 像素检查、OCR、完整符号等价证明或独立重算；这些属于后续能力或前置验证职责。

## 21. 当前测试状态
V1.0-B 的代码、Schema、治理规范与回归测试已写入 GitHub。当前环境没有实际执行 pytest，因此不能声称测试通过。

## 22. 后续 V1.0-C
下一阶段应从“引用闭环”进入“可重建性闭环”：从 ProblemSpec/原始附件/代码/环境重新执行关键计算，与冻结 ResultBundle 做独立重建比较，并把重建差异纳入最终 Gate。