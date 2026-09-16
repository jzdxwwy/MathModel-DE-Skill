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
- 06 Verification：通用核验 + Domain Rule Registry + Mathematical Acceptance + Independent Recompute + Evidence Lineage + Rendered Consistency + Presentation Materialization + Reproducibility Manifest + Environment Closure → VerificationReport
- 07 Writing：PaperEvidence Gate 与 Presentation Gate 通过后才允许冻结证据并写论文；PaperManifest 规定论文结构与证据映射
- 08 Final Submission：Final Submission Gate 汇总验证、展示物化、论文、环境闭包与交付文件，决定最终是否允许标记提交完成

## 3. D/E 定位
D/E 是先验，不是固定模板。先识别 prediction、evaluation、optimization、classification、clustering、simulation、mechanism、network、risk、comprehensive_decision 等任务类型，再结合 D/E 知识缩小模型空间。

## 4. Runtime / Gate
`Input Boundary → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Deterministic Binding → ToolDispatch → ToolRegistry → Numerical Adapter → ResultBundle → Domain Rule Registry → Mathematical Acceptance → Independent Recompute → Evidence Lineage → PaperEvidence → Presentation Evidence → Rendered Consistency → Presentation Materialization → Render Manifest → PaperManifest → SubmissionManifest → Cross-Artifact Consistency → Environment Closure → Reproducibility Gate → Writing → Final Submission Gate`

Gate：`Analysis → Data → Model → Binding → Compute → Verification → PaperEvidence → Presentation → RenderedConsistency → Materialization → EnvironmentClosure → Reproducibility → CrossArtifactConsistency → Writing → FinalSubmission`。任何关键 Gate 未通过不得标记完成。

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

## 22. V1.0-D：Automatic Clean Rebuild
V1.0-D 把 V1.0-C 中“人工提供 rebuild_dir”的机制推进到 Runtime 层。

核心链：
`Frozen Run → RebuildContract → Input Hash Verification → Registered Tool → Fresh Rebuild Run → Rebuilt ResultBundle → V1.0-C Reproducibility Gate`

新增：
- `artifacts/schemas/rebuild-contract.schema.json`
- `tools/runtime/rebuild_engine.py`
- `tests/verification/test_v10_d_rebuild_engine.py`
- `00_governance/V1_0_D_AUTOMATIC_CLEAN_REBUILD.md`

V1.0-D 的硬约束：
- RebuildContract 必须明确 reference run、model、registered tool、输入文件 SHA256、参数、环境和预期结果身份；
- 输入文件 hash 不一致 → `BLOCKED/FAIL`，不得继续执行；
- tool 不在 `ToolRegistry` → `BLOCKED/FAIL`；
- 禁止 arbitrary shell，禁止通过 contract 注入自由命令；
- 每次重建使用新的 `rebuild-*` run 目录；
- Frozen/reference ResultBundle 不得被覆盖或修改；
- Runtime 产生的重建 ResultBundle 仍必须交给 V1.0-C 做确定性结果比较；
- GitHub 中写入 Runtime 代码不等于已经完成一次真实重建，真实执行必须由受信任 Host/Runtime 提供 ToolRegistry。

因此 V1.0-D 不是“自动跑任意代码”，而是把可执行边界锁定在已有的 ToolRegistry 上，形成可审计的 clean rebuild。

## 23. V1.0-E：Environment Closure / Clean-Room Rebuild
V1.0-E 进一步解决“代码和输入相同，但运行环境不同”的可复现性缺口。

核心链：
`Frozen Run → EnvironmentClosure → Deterministic Fingerprint → Clean-Room Environment → Automatic Rebuild → Rebuilt EnvironmentClosure → Environment Gate → V1.0-C Reproducibility`

新增：
- `artifacts/schemas/environment-closure.schema.json`
- `artifacts/schemas/environment-gate.schema.json`
- `tools/runtime/environment_closure.py`
- `tools/verification/environment_gate.py`
- `tests/verification/test_v10_e_environment.py`
- `00_governance/V1_0_E_ENVIRONMENT_CLOSURE.md`

EnvironmentClosure 冻结：
- Python implementation/version；
- OS / architecture；
- 声明的 package versions；
- registered tool 的 code reference/hash；
- source files SHA256；
- 完整 input files SHA256；
- model/spec references；
- network/shell/isolation policy；
- deterministic environment fingerprint。

V1.0-E 的硬约束：
- reference closure 缺失或不完整 → `NOT_RUN`；
- closure fingerprint 自洽失败 → `FAIL`；
- rebuild closure 缺失 → `NOT_RUN`；
- environment 字段明确不一致 → `FAIL`；
- complete 且一致 → `PASS`；
- `NOT_RUN` 不得升级为 `PASS`；
- 环境元数据不等于真正的隔离执行证据；真实 clean-room execution 必须由受信任 Host/EnvironmentAdapter 完成；
- 不硬编码 Docker/Conda/venv，不允许环境闭包模块自行执行 arbitrary shell/network；
- reference ResultBundle 与 reference EnvironmentClosure 均不可被重建过程修改。

Final Submission Gate 新增 `F8_ENVIRONMENT_CLOSURE`，默认要求环境闭包通过。这样最终提交级 PASS 的证据链变成：结果正确、验证通过、展示一致、跨 Artifact 一致、独立重建一致、环境闭包一致。

## 24. 当前测试状态
V1.0-E 的代码、Schema、治理规范与回归测试已写入 GitHub。当前环境没有实际执行 pytest，因此不能声称 V1.0-C/D/E 测试通过；GitHub 文件成功写入也不等于运行时验证成功。

## 25. 下一阶段
V1.0-F 应把 Environment Closure 从“记录与比较”继续推进到 **Environment Adapter / Dependency Lock / Clean-Room Execution Evidence**：由受信任 Host 提供可插拔的 Docker/Conda/venv/CI 等适配器，冻结依赖锁文件、环境镜像/解释器指纹，并把真实隔离执行日志与重建结果绑定起来。在此之前，不应声称已经实现真正的 clean-room execution。
