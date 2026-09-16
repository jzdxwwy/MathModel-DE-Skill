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
`Input Boundary → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Deterministic Binding → ToolDispatch → ToolRegistry → Numerical Adapter → ResultBundle → Domain Rule Registry → Mathematical Acceptance → Independent Recompute → Evidence Lineage → PaperEvidence → Presentation Evidence → Rendered Consistency → Presentation Materialization → Render Manifest → PaperManifest → SubmissionManifest → Cross-Artifact Consistency → Reproducibility Gate → Writing → Final Submission Gate`

Gate：`Analysis → Data → Model → Binding → Compute → Verification → PaperEvidence → Presentation → RenderedConsistency → Materialization → Reproducibility → CrossArtifactConsistency → ReproducibilityGate → Writing → FinalSubmission`。任何关键 Gate 未通过不得标记完成。

## 5–19. 已有版本
V0.8–V1.0 首版能力保持不变，具体实现与治理文件见仓库对应版本文档。

## 20. V1.0-B：Cross-Artifact Consistency Gate
V1.0-B 解决“每个 Artifact 单独合法，但彼此引用错位”的问题。

核心链：
`PaperManifest → PaperEvidence → PresentationDataManifest → ResultBundle → VerificationReport`
并同时检查：
`PresentationDataManifest → RenderManifest → SubmissionManifest → 实际交付文件`

新增 B01–B08 跨 Artifact 检查，并把 `F6_CROSS_ARTIFACT` 接入 Final Submission Gate。

## 21. V1.0-C：Reproducibility Gate
V1.0-C 将能力从“可追溯、可交叉引用”推进到“可独立重建”。

核心链：
`Frozen ResultBundle → Rebuild Contract → Independent Rebuild → Rebuilt ResultBundle → Deterministic Comparison → Reproducibility Gate`

新增：
- `tools/verification/reproducibility_gate.py`
- `artifacts/schemas/reproducibility-gate.schema.json`
- `tests/verification/test_v10_reproducibility_gate.py`
- `00_governance/V1_0_C_REPRODUCIBILITY_GATE.md`

V1.0-C 的原则：
- 没有独立重建证据 → `NOT_RUN`；
- 提供重建目录但缺少 ResultBundle → `FAIL`；
- 原始 Frozen ResultBundle 永不覆盖；
- 独立比较 `model_id`、output 名称、数值、单位和 metrics；
- 数值比较采用显式 `atol=1e-8`、`rtol=1e-6`；
- 必要源文件 SHA256 发生变化 → `FAIL`；
- 不允许 LLM 将 `NOT_RUN` 擅自升级为 `PASS`。

V1.0 Final Submission Gate 已新增 `F7_REPRODUCIBILITY`，默认要求 V1.0-C 通过。也就是说，最终提交级 PASS 不再仅代表“证据齐全”，还要求存在独立重建并与冻结结果一致。

当前 C 是**确定性验收器**，不直接执行任意项目代码。后续可以继续增加容器化环境、依赖锁定、clean-room rebuild、数据集 hash closure 和 command replay。

## 22. 当前测试状态
V1.0-C 的代码、Schema、治理规范与回归测试已写入 GitHub。当前环境没有实际执行 pytest，因此不能声称测试通过。

## 23. 后续 V1.0-D
下一阶段应把“独立重建”真正接入 Runtime：自动生成 Rebuild Contract，冻结输入/代码/环境，执行 clean rebuild，并将重建产物直接送入 V1.0-C Gate，而不是依赖人工提供 rebuild 目录。
