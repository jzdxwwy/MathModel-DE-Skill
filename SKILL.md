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
`Input Boundary → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Deterministic Binding → ToolDispatch → ToolRegistry → Numerical Adapter → ResultBundle → Domain Rule Registry → Mathematical Acceptance → Independent Recompute → Evidence Lineage → PaperEvidence → Presentation Evidence → Rendered Consistency → Presentation Materialization → Render Manifest → PaperManifest → SubmissionManifest → Writing → Final Submission Gate`

Gate：`Analysis → Data → Model → Binding → Compute → Verification → PaperEvidence → Presentation → RenderedConsistency → Materialization → Reproducibility → Writing → FinalSubmission`。任何关键 Gate 未通过不得标记完成。

## 5. V0.8
确定性模型选择器按七维评分选择模型：fit 25、data 15、constraints 15、interpretability 15、verifiability 15、robustness 10、cost 5。LLM 不能覆盖选择结果或任意发明工具。

## 6. V0.9-B
已建立显式 `data_binding`、统一 Template Adapter、ToolExecutionEngine 和正式 ResultBundle。缺少绑定或暂不支持时 `INPUT_BLOCKED`。

## 7. V0.9-C：数学输入契约与数值适配器
V0.9-C 把“Python 模板存在”推进为“数学输入可计算”：时间序列、最短路径、事件流/轨迹、显式优化、敏感性、Monte Carlo 均有受控适配器。

关键安全规则：LLM 只能提供结构化 binding，不能提交 Python；表达式执行使用白名单函数；缺少完整数学输入契约就阻断。

## 8. V0.9-D：确定性自动 Binding
核心链：`DataProfile → Binding Resolver → Binding Gate → ModelSpec/ToolDispatch → Compute`。

Binding Resolver 只使用 DataProfile 的确定性事实和已验证语义角色；回归/分类/时间序列/网络可以在满足唯一性和字段契约时自动绑定。优化、敏感性、Monte Carlo、机理模拟无法安全推导数学表达式时必须 `BLOCKED`，不能猜。

LLM 可以提出语义提示，但不能覆盖确定性模型选择，也不能绕过 Binding Gate。`BLOCKED → INPUT_BLOCKED` 是正常的 fail-closed 状态。

## 9. V0.9-E：ResultBundle → VerificationReport
V0.9-E 建立通用结果验证器与执行桥，检查运行完整性、ResultBundle 状态、有限数值、模型一致性、Binding 状态及证据缺失。

## 10. V0.9-F：Domain Verification Rules
V0.9-F 新增 `tools/verification/domain_verifier.py`，并将其接入 `result_verifier.py`。验证按模型族读取真实证据。

规则采用 **evidence-first**：缺少指标或证据只能得到 `NOT_RUN`，不能被模型名称或经验自动补成 PASS。

## 11. V0.9-G：Domain Verification Rule Registry
V0.9-G 将领域验证从条件分支升级为注册式架构：

`ResultBundle → Generic Verification → Rule Registry → Domain Rule Set → VerificationReport → Gate`

新增 `tools/verification/rule_registry.py`、`tools/verification/default_rules.py` 和 `00_governance/V0_9_G_RULE_REGISTRY.md`。当前规则集覆盖 regression、classification、time-series、optimization、network、stochastic、mechanism。未注册模型保持 `NOT_RUN`。

## 12. V0.9-H：Schema-driven Mathematical Acceptance
V0.9-H 将验证从“证据存在性”推进到“数学验收”，使用 `verification-rule.schema.json` 与 `rule_evaluator.py` 执行数学不变量、数值范围和证据绑定检查。

明确违反数学不变量 → `FAIL`；缺少足够证据 → `NOT_RUN`；证据充分且满足规则 → `PASS`。V0.9-H 不是符号定理证明器。

## 13. V0.9-I：Evidence Materialization + Independent Recompute
V0.9-I 将 Verification 从“检查模型自己报告的数字”推进到“独立复算数字”。`tools/verification/recompute_engine.py` 在原始证据存在时独立复算关键指标，并把结果与 ResultBundle 比较；缺少原始证据保持 `NOT_RUN`。

当前支持回归 MAE/RMSE/R²、分类 Accuracy。独立复算绝不覆盖原始 ResultBundle。

## 14. V0.9-J：Independent Recompute Expansion + Evidence Lineage
V0.9-J 将独立复算扩展到更多模型族，并建立第一版 Evidence Lineage 图。

核心链：`Raw Input → DataProfile → ModelSpec → RunManifest → ResultBundle → Independent Recompute → VerificationReport → PaperEvidence`

新增独立复算扩展、EvidenceLineage Schema、确定性 lineage builder、治理规范和测试夹具。EvidenceLineage 使用 typed nodes：`input/data/model/run/result/verification/paper_evidence/figure`；关系必须有显式依据，不能猜测。

## 15. V0.9-K：PaperEvidence First-Class Artifact + Evidence Lineage Gate
V0.9-K 将 `PaperEvidence` 从写作阶段的普通中间对象升级为一等 Artifact，并建立强制证据门禁。

核心链：`ResultBundle → VerificationReport → EvidenceLineage → PaperEvidence → PaperEvidence Gate → Writing`

每个 material claim 必须具有 `verification_refs`、`result_refs`、`lineage_refs`。只有 PaperEvidence Gate=`PASS` 才允许进入冻结状态。

## 16. V0.9-L：Figure / Table / Equation Evidence Binding
V0.9-L 把论文中的三类呈现对象正式纳入证据体系：

`Figure / Table / Equation → source_refs → result_refs → verification_refs → lineage_refs`

新增 `artifacts/schemas/paper-presentation.schema.json`、`tools/verification/presentation_evidence.py`、`tools/verification/evidence_lineage.py`、`00_governance/V0_9_L_PRESENTATION_EVIDENCE.md` 与测试夹具。每个图、表、公式必须明确绑定来源、结果、验证报告和 lineage；任何引用缺失或无法解析都为 `FAIL`。

## 17. V0.9-M：Rendered Artifact Consistency
V0.9-M 将“证据绑定”进一步推进为“展示内容与权威计算结果逐项一致”。核心链：

`ResultBundle / ModelSpec → PresentationDataManifest → Rendered Consistency Verifier → PresentationConsistencyReport → Presentation Gate`

新增：
- `artifacts/schemas/presentation-data-manifest.schema.json`
- `tools/verification/rendered_consistency.py`
- `00_governance/V0_9_M_RENDERED_CONSISTENCY.md`
- `tests/verification/test_v09_m.py`

当前检查：表格物化数值与 ResultBundle output/metric 的一致性及容差；图表数据 binding 是否可解析到 ResultBundle；公式的 ModelSpec 引用及规范化表达式 hash 一致性。

V0.9-M 不做像素级图像比较、OCR 全表格复核或完整符号代数等价证明；它验证的是**渲染前的确定性数据契约**。缺失或无法解析的 publishable presentation binding → `FAIL`。

## 18. V0.9-N：Reproducible Presentation / Submission Pipeline
V0.9-N 将 PresentationDataManifest 从“校验输入”升级为“展示生成的唯一数据源”，并进一步建立论文结构映射与运行级可复现交付索引。

核心链：

`ResultBundle → PresentationDataManifest → Rendered Consistency → Materialized Presentation Payload → Render Manifest / SHA256 → Renderer → PaperManifest → Paper → SubmissionManifest`

新增：
- `tools/verification/presentation_materializer.py`
- `artifacts/schemas/presentation-render-manifest.schema.json`
- `tools/writing/paper_manifest_builder.py`
- `artifacts/schemas/paper-manifest.schema.json`
- `tools/submission/submission_manifest.py`
- `artifacts/schemas/submission-manifest.schema.json`
- `00_governance/V0_9_N_PRESENTATION_MATERIALIZATION.md`
- `tests/verification/test_v09_n.py`
- `tests/verification/test_v09_n_upgrade.py`

物化器只解析 manifest 中已声明的 binding，不重新计算、不猜测、不修改 ResultBundle。payload 记录源 PresentationDataManifest hash 与 ResultBundle hash，并生成 SHA256；Render Manifest 记录每个 render input 的 hash。`PaperManifest` 只规定章节与 claim/figure/table/equation/render 的引用关系，不生成未经证据约束的正文。`SubmissionManifest` 记录 run、环境、已存在 artifact 的路径与 SHA256，以及上游 manifest/report 引用。

V0.9-N 已接入 `tools/runtime/verification_engine.py`：V0.9-M 一致性通过后才执行 materialization，并在每个 run 生成 `submission-manifest.json`。缺失显式要求的交付 artifact 或 materialization 失败时必须 fail-closed。

## 19. V1.0：Final Submission Gate
V1.0 将此前分散的 Verification、Presentation、Materialization、PaperManifest 与 SubmissionManifest 收束为最终交付门禁。

核心链：

`VerificationReport → PresentationRenderManifest → PaperManifest → SubmissionManifest → FinalSubmissionGateReport → Final Submission`

新增：
- `artifacts/schemas/final-submission-gate.schema.json`
- `tools/verification/final_submission_gate.py`
- `tests/verification/test_v10_final_submission_gate.py`
- `00_governance/V1_0_FINAL_SUBMISSION_GATE.md`

首版 Final Gate 检查：
- ResultBundle 是否存在且为 `VALIDATED/FROZEN`；
- VerificationReport 是否真实 `PASS`；
- PresentationRenderManifest 是否真实 `PASS`；
- SubmissionManifest 是否存在；
- 调用方显式要求的 artifact 是否存在；
- 若要求论文交付，论文文件是否存在。

决策规则严格为：任一 `FAIL` → `FAIL`；无 `FAIL` 但存在 `NOT_RUN` → `NOT_RUN`；全部必要检查 `PASS` → `PASS`。V1.0 首版不把 `NOT_RUN` 自动升级为 PASS。

Final Gate 不重新计算模型、不修改 ResultBundle、不伪造 hash；数学正确性仍由前置 Verification / Domain Rules / Independent Recompute 负责。

## 20. 当前测试状态
V1.0 首版代码、Schema、治理规范与回归测试已写入 GitHub。当前环境没有实际执行 pytest，因此不能声称测试通过。

## 21. 后续 V1.0 增强
下一步不是增加更多模型，而是继续把 Final Gate 做成真正的“提交验收器”：接入真实 PaperEvidence Gate、Presentation Gate、PaperManifest 引用闭环、Word/PDF/ZIP 完整性检查，并最终实现可重建性检查。
