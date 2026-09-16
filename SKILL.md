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
- 06 Verification：通用核验 + Domain Rule Registry + Mathematical Acceptance + Independent Recompute + Evidence Lineage + Rendered Consistency + Presentation Materialization + Reproducibility + Environment Closure + Clean-Room Evidence + Execution Evidence + Execution Replay → VerificationReport
- 07 Writing：PaperEvidence Gate 与 Presentation Gate 通过后才允许冻结证据并写论文；PaperManifest 规定论文结构与证据映射
- 08 Final Submission：Final Submission Gate 汇总验证、展示物化、论文、环境闭包、Clean-Room Execution Evidence、Execution Replay 与交付文件，决定最终是否允许标记提交完成

## 3. D/E 定位
D/E 是先验，不是固定模板。先识别 prediction、evaluation、optimization、classification、clustering、simulation、mechanism、network、risk、comprehensive_decision 等任务类型，再结合 D/E 知识缩小模型空间。

## 4. Runtime / Gate
`Input Boundary → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Deterministic Binding → ToolDispatch → ToolRegistry → Numerical Adapter → ResultBundle → Domain Rule Registry → Mathematical Acceptance → Independent Recompute → Evidence Lineage → PaperEvidence → Presentation Evidence → Rendered Consistency → Presentation Materialization → Render Manifest → PaperManifest → SubmissionManifest → Cross-Artifact Consistency → Environment Closure → Environment Adapter → Dependency Lock → Trusted Adapter Registry → Trusted Host → Clean-Room Execution → Execution Evidence → Execution Replay → Reproducibility Gate → Writing → Final Submission Gate`

Gate：`Analysis → Data → Model → Binding → Compute → Verification → PaperEvidence → Presentation → RenderedConsistency → Materialization → EnvironmentClosure → EnvironmentAdapter → DependencyLock → AdapterTrust → CleanRoomEvidence → ExecutionEvidence → ExecutionReplay → Reproducibility → CrossArtifactConsistency → Writing → FinalSubmission`。任何关键 Gate 未通过不得标记完成。

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

核心链：`EnvironmentClosure → EnvironmentAdapterContract → Trusted Host Adapter → Isolated Execution → Observed EnvironmentClosure → CleanRoomGate → ReproducibilityGate`。

适配器类型抽象为 `HOST/VENV/CONDA/DOCKER/GITHUB_ACTIONS/CUSTOM`，但类型不代表 Runtime 已经拥有对应环境。

## 25. V1.0-G：Dependency Lock + Trusted Host Execution
V1.0-G 建立 Dependency Lock、Adapter Registry、TrustedHost 与 ExecutionEvidence。只有显式 trusted adapter 才能进入执行边界；shell/network 默认禁止；ExecutionEvidence 闭合 adapter、isolation、lock、environment、tool、input、log 与 ResultBundle。

## 26. V1.0-H：Controlled Execution Replay
V1.0-H 把 V1.0-G 的“执行证据接口”推进到**受控的实际工具回放路径**。

### 26.1 ExecutionReplayContract
新增 `artifacts/schemas/execution-replay-contract.schema.json`。

Contract 明确冻结：
- run_id；
- adapter_id；
- ToolRegistry 中的 tool；
- 完整 input SHA256；
- expected dependency-lock hash；
- expected environment fingerprint；
- `allow_network=false`；
- `allow_shell=false`；
- isolation policy；
- 已声明 payload。

### 26.2 ExecutionReplayEngine
新增 `tools/runtime/execution_replay.py`。

执行顺序：
`Trusted Adapter Validation → Registered Tool Validation → Lock/Environment Check → Input Hash Check → Registered Tool Invocation → New ResultBundle → Execution Log → Hash-linked ExecutionReplayResult`。

这里的“执行”不是 shell 执行，而是对 **ToolRegistry 已注册 callable** 的受控调用。这样既形成真正的 runtime replay，又保持核心 Skill 不允许模型生成任意命令。

reference ResultBundle 永远不被覆盖；replay 输出写入独立目录。

### 26.3 ExecutionReplayResult
新增 `artifacts/schemas/execution-replay-result.schema.json`。

证据必须闭合：
`adapter_id + isolation_id + lock_hash + environment_fingerprint + input_hashes + execution_log_sha256 + result_bundle_sha256`。

### 26.4 Execution Replay Gate
新增 `tools/verification/execution_replay_gate.py`。

Gate 检查：
- `EXECUTED` 状态；
- ResultBundle hash；
- execution log hash；
- adapter/tool identity；
- isolation identity；
- dependency lock hash；
- environment fingerprint。

缺少 replay evidence → `NOT_RUN`；证据不一致 → `FAIL`；完整闭包 → `PASS`。

### 26.5 Final Submission Gate
新增 F10 `EXECUTION_REPLAY`。V1.0-H 默认要求 Execution Replay 通过，因此即使 V1.0-G 的 execution evidence 存在，没有实际 replay 证据仍不能进入最终 PASS。

## 27. 安全与不可伪造原则
- 不允许 LLM 直接生成并执行任意 shell/install 命令；
- network/shell 默认关闭；
- adapter kind 不等于真实执行；
- EnvironmentClosure 不等于 execution evidence；
- ExecutionReplay 只能调用已注册 ToolRegistry；
- lock、environment、log、ResultBundle 均通过 SHA256 闭合；
- Frozen ResultBundle 与 reference artifacts 永不被重建覆盖；
- GitHub connector 成功写文件不等于 clean-room execution 已发生；
- 真实 Docker/Conda/venv OS 级隔离仍由受信任 Host 的具体实现负责。

## 28. 当前测试状态
V1.0-H 的 Schema、ExecutionReplayEngine、ExecutionReplayGate、Final Submission Gate F10、治理规范与回归测试已写入 GitHub。本次会话没有在真实 Runtime 中执行 pytest，也没有创建 Docker/Conda/venv 隔离环境，因此不能声称 V1.0-H 测试或真实 OS 级 clean-room execution 已通过。

## 29. 下一阶段
V1.0-I 应进入 **Concrete Host Materialization**：在真正受信任的执行机上落地至少一种具体后端，例如 Python venv，并将 DependencyLock Materialization、真实 package installation、environment inventory、ToolRegistry replay、observed EnvironmentClosure 与 V1.0-C Reproducibility 自动串起来。核心 Skill 仍保持无 arbitrary shell、无默认网络、证据闭包优先。
