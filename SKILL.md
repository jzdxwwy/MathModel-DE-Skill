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
- 04 Compute：Binding Gate → ToolDispatch → ToolRegistry → 数值执行 → RunManifest/ResultBundle
- 05 Visualization：真实结果 → Figure/Table/Equation Evidence Binding → Presentation Data Manifest → Materialization → Render Manifest → PaperEvidence
- 06 Verification：通用核验 + Domain Rule Registry + Mathematical Acceptance + Independent Recompute + Evidence Lineage + Rendered Consistency + Presentation Materialization + Reproducibility + Environment Closure + Clean-Room Evidence + Execution Evidence → VerificationReport
- 07 Writing：PaperEvidence Gate 与 Presentation Gate 通过后才允许冻结证据并写论文；PaperManifest 规定论文结构与证据映射
- 08 Final Submission：Final Submission Gate 汇总验证、展示物化、论文、环境闭包、Clean-Room Execution Evidence 与交付文件，决定最终是否允许标记提交完成

## 3. D/E 定位
D/E 是先验，不是固定模板。先识别 prediction、evaluation、optimization、classification、clustering、simulation、mechanism、network、risk、comprehensive_decision 等任务类型，再结合 D/E 知识缩小模型空间。

## 4. Runtime / Gate
`Input Boundary → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Deterministic Binding → ToolDispatch → ToolRegistry → Numerical Adapter → ResultBundle → Domain Rule Registry → Mathematical Acceptance → Independent Recompute → Evidence Lineage → PaperEvidence → Presentation Evidence → Rendered Consistency → Presentation Materialization → Render Manifest → PaperManifest → SubmissionManifest → Cross-Artifact Consistency → Environment Closure → Environment Adapter → Dependency Lock → Trusted Adapter Registry → Trusted Host → Clean-Room Execution → Execution Evidence → Reproducibility Gate → Writing → Final Submission Gate`

Gate：`Analysis → Data → Model → Binding → Compute → Verification → PaperEvidence → Presentation → RenderedConsistency → Materialization → EnvironmentClosure → EnvironmentAdapter → DependencyLock → AdapterTrust → CleanRoomEvidence → ExecutionEvidence → Reproducibility → CrossArtifactConsistency → Writing → FinalSubmission`。任何关键 Gate 未通过不得标记完成。

## 5–19. 已有版本
V0.8–V1.0 首版能力保持不变，具体实现与治理文件见仓库对应版本文档。

## 20. V1.0-B：Cross-Artifact Consistency Gate
V1.0-B 解决“每个 Artifact 单独合法，但彼此引用错位”的问题。核心链：`PaperManifest → PaperEvidence → PresentationDataManifest → ResultBundle → VerificationReport`，并检查 `PresentationDataManifest → RenderManifest → SubmissionManifest → 实际交付文件`。

## 21. V1.0-C：Reproducibility Gate
V1.0-C 将能力推进到可独立重建：`Frozen ResultBundle → Rebuild Contract → Independent Rebuild → Rebuilt ResultBundle → Deterministic Comparison → Reproducibility Gate`。没有独立重建证据为 `NOT_RUN`，不允许升级为 `PASS`；Frozen ResultBundle 永不覆盖；数值比较采用显式 `atol=1e-8`、`rtol=1e-6`。

## 22. V1.0-D：Automatic Clean Rebuild
V1.0-D 将 rebuild_dir 机制推进到 Runtime：`Frozen Run → RebuildContract → Input Hash Verification → Registered Tool → Fresh Rebuild Run → Rebuilt ResultBundle → V1.0-C Reproducibility Gate`。禁止 arbitrary shell，tool 必须注册，reference ResultBundle 不得修改。

## 23. V1.0-E：Environment Closure / Clean-Room Rebuild
V1.0-E 解决“代码和输入相同，但运行环境不同”的可复现性缺口。EnvironmentClosure 冻结 Python、平台、声明依赖、tool/source/input hash、model/spec refs 与安全策略，并生成 deterministic fingerprint。环境元数据本身不等于真实隔离执行。

## 24. V1.0-F：Environment Adapter / Clean-Room Evidence
V1.0-F 把 V1.0-E 的“环境记录与比较”推进到可插拔的执行边界。

核心链：
`EnvironmentClosure → EnvironmentAdapterContract → Trusted Host Adapter → Isolated Execution → Observed EnvironmentClosure → CleanRoomGate → ReproducibilityGate`

新增：`environment-adapter.schema.json`、`environment_adapter.py`、`clean_room_gate.py`、对应测试与治理规范。适配器类型抽象为 `HOST/VENV/CONDA/DOCKER/GITHUB_ACTIONS/CUSTOM`，但类型不代表 Runtime 已经拥有对应环境。

## 25. V1.0-G：Dependency Lock + Trusted Host Execution
V1.0-G 把“可声明的环境边界”推进到**可审计的真实执行证据接口**，但不把 GitHub 文件操作或模型生成命令冒充为执行。

### 25.1 DependencyLockManifest
新增 `artifacts/schemas/dependency-lock-manifest.schema.json` 与 `tools/runtime/dependency_lock.py`。

锁定：
- Python implementation/version；
- package name/version/source/hash；
- tool name/version/ref；
- 可选 base image；
- source file SHA256；
- deterministic fingerprint。

Lock 是声明性、可哈希材料；核心 Skill 不调用 pip/conda/docker。

### 25.2 Trusted Adapter Registry
新增 `environment-adapter-registry.schema.json` 与 `tools/runtime/adapter_registry.py`。

只有显式 `trusted=true` 的 adapter 才能被 TrustedHost 接受；未知 adapter、未信任 adapter、带 shell/network 能力的 adapter 必须阻断。

### 25.3 TrustedHost
新增 `tools/runtime/trusted_host.py`。

TrustedHost 是受控运行时的接口边界。当前仓库只提供能力验证与阻断式默认 `execute()`；真实 Docker/Conda/venv/CI 执行必须由外部可信 Host 注入实现。这样可以避免把 LLM 生成的字符串直接变成任意 shell 命令。

### 25.4 ExecutionEvidence
新增 `artifacts/schemas/execution-evidence.schema.json` 与 `tools/verification/execution_evidence_gate.py`。

真实 clean-room execution 必须闭合：
`adapter_id + isolation_id + lock_hash + environment_fingerprint + tool_ref + input_hashes + execution_log_hash + result_bundle_hash + observed_at`。

Gate 语义：
- 缺少 evidence → `NOT_RUN`；
- 执行失败或任一关键 hash 不一致 → `FAIL`；
- 所有执行证据闭合 → `PASS`。

### 25.5 Final Submission Gate
F9 `CLEAN_ROOM_EXECUTION` 已接入 Final Submission Gate，并默认要求通过。没有真实 TrustedHost execution evidence 时，最终 Gate 不得 PASS。

## 26. 安全与不可伪造原则
- 不允许 LLM 直接生成并执行任意 shell/install 命令；
- network/shell 默认关闭；
- adapter kind 不等于真实执行；
- EnvironmentClosure 不等于 execution evidence；
- ExecutionEvidence 中的 lock、environment、log、ResultBundle 均通过 SHA256 闭合；
- Frozen ResultBundle 与 reference artifacts 永不被重建覆盖；
- GitHub connector 成功写文件不等于 clean-room execution 已发生。

## 27. 当前测试状态
V1.0-G 的 Schema、Runtime boundary、Dependency Lock、Adapter Registry、TrustedHost、Execution Evidence Gate、Final Submission Gate 集成、治理规范与回归测试已写入 GitHub。本次会话没有在真实 Runtime 中执行 pytest，也没有创建 Docker/Conda/venv 隔离环境，因此不能声称 V1.0-G 测试或真实 clean-room execution 已通过。

## 28. 下一阶段
V1.0-H 应聚焦 **真实 Host Adapter Materialization + Execution Replay**：在受控 Host 上实现至少一种具体隔离后端，并把 lock materialization、tool invocation、execution log、observed closure、ResultBundle、execution evidence 与 V1.0-C reproducibility 串成一次可重放运行。核心 Skill 继续保持“无 arbitrary shell、无默认网络、证据闭包优先”。
