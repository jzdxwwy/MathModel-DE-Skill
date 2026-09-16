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
- 08 Final Submission：Final Submission Gate 汇总验证、展示物化、论文、环境闭包、Clean-Room Execution Evidence、Execution Replay、Host Materialization 与交付文件，决定最终是否允许标记提交完成

## 3. D/E 定位
D/E 是先验，不是固定模板。先识别 prediction、evaluation、optimization、classification、clustering、simulation、mechanism、network、risk、comprehensive_decision 等任务类型，再结合 D/E 知识缩小模型空间。

## 4. Runtime / Gate
`Input Boundary → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Deterministic Binding → ToolDispatch → ToolRegistry → Numerical Adapter → ResultBundle → Domain Rule Registry → Mathematical Acceptance → Independent Recompute → Evidence Lineage → PaperEvidence → Presentation Evidence → Rendered Consistency → Presentation Materialization → Render Manifest → PaperManifest → SubmissionManifest → Cross-Artifact Consistency → Environment Closure → Environment Adapter → Dependency Lock → Trusted Adapter Registry → Trusted Host → Concrete Host Materialization → Clean-Room Execution → Execution Evidence → Execution Replay → Reproducibility Gate → Writing → Final Submission Gate`

Gate：`Analysis → Data → Model → Binding → Compute → Verification → PaperEvidence → Presentation → RenderedConsistency → Materialization → EnvironmentClosure → EnvironmentAdapter → DependencyLock → AdapterTrust → HostMaterialization → CleanRoomEvidence → ExecutionEvidence → ExecutionReplay → Reproducibility → CrossArtifactConsistency → Writing → FinalSubmission`。任何关键 Gate 未通过不得标记完成。

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

Contract 明确冻结：run_id、adapter_id、ToolRegistry 中的 tool、完整 input SHA256、expected dependency-lock hash、expected environment fingerprint、`allow_network=false`、`allow_shell=false`、isolation policy 与已声明 payload。

### 26.2 ExecutionReplayEngine
新增 `tools/runtime/execution_replay.py`。执行顺序：`Trusted Adapter Validation → Registered Tool Validation → Lock/Environment Check → Input Hash Check → Registered Tool Invocation → New ResultBundle → Execution Log → Hash-linked ExecutionReplayResult`。

这里的“执行”不是 shell 执行，而是对 **ToolRegistry 已注册 callable** 的受控调用。reference ResultBundle 永远不被覆盖；replay 输出写入独立目录。

### 26.3 Execution Replay Gate
新增 `tools/verification/execution_replay_gate.py`。缺少 replay evidence → `NOT_RUN`；证据不一致 → `FAIL`；完整闭包 → `PASS`。Final Submission Gate 使用 F10 `EXECUTION_REPLAY`。

## 27. V1.0-I：Concrete Host Materialization
V1.0-I 首次把“受信任 Host”从抽象接口推进到一个**真实可创建的 Python venv**，但明确不把 venv 创建冒充为完整 clean-room execution。

### 27.1 VenvMaterializationContract
新增 `artifacts/schemas/venv-materialization-contract.schema.json`，冻结：
- `adapter_id`；
- Python implementation/version；
- fresh target directory；
- DependencyLock fingerprint；
- `allow_network=false`；
- `allow_shell=false`；
- `isolation_required=true`。

### 27.2 Concrete venv Adapter
新增 `tools/runtime/venv_adapter.py`。它只调用 Python 标准库 `venv.EnvBuilder` 创建全新的虚拟环境，不调用 shell、pip、conda、docker，也不接受模型生成的命令。

创建后记录 `VenvMaterializationEvidence`：目标目录、解释器路径、Python/host 信息、lock hash、解释器 SHA256 与 evidence fingerprint。

### 27.3 Materialization Gate
新增 `tools/verification/materialization_gate.py`。要求 fresh、策略关闭 network/shell、解释器真实存在、lock hash 与 interpreter hash 均存在；缺证据为 `NOT_RUN`，矛盾证据为 `FAIL`。

### 27.4 Final Submission Gate
新增 F11 `HOST_MATERIALIZATION`。因此最终提交链现在是：
`F9 Clean-Room Execution → F10 Execution Replay → F11 Host Materialization → Reproducibility`。

## 28. 安全与不可伪造原则
- 不允许 LLM 直接生成并执行任意 shell/install 命令；
- network/shell 默认关闭；
- adapter kind 不等于真实执行；
- EnvironmentClosure 不等于 execution evidence；
- ExecutionReplay 只能调用已注册 ToolRegistry；
- V1.0-I venv 只负责环境创建，不负责任意 package installation；
- lock、environment、log、ResultBundle 均通过 SHA256 闭合；
- Frozen ResultBundle 与 reference artifacts 永不被重建覆盖；
- GitHub connector 成功写文件不等于 clean-room execution 已发生；
- Python venv 是 Python 环境隔离，不等于 Docker/OS 级安全隔离；
- 真实 package installation 与 venv 内跨进程 ToolRegistry execution 仍必须由受信任 Host 的固定入口实现。

## 29. 当前测试状态
V1.0-I 的 Contract、Venv Adapter、Materialization Evidence、Materialization Gate、F11 Final Submission Gate 与回归测试已写入 GitHub。本次会话没有在真实 Runtime 中执行 pytest，也没有在真实执行机创建 venv，因此不能声称 V1.0-I 已运行通过。当前实现已经具备可执行的 venv materialization 单元边界，但尚未完成锁定依赖安装和 venv 内模型工具执行。

## 30. 下一阶段
V1.0-J 应进入 **Locked Dependency Installation + Observed Environment Inventory**：使用受信任 Host 的固定 argv 安装器严格依据 DependencyLockManifest 安装依赖，禁止模型生成安装命令；安装后从 venv 自身解释器采集 package inventory，并与 lock 做确定性比较。随后再把 V1.0-H ExecutionReplay 接到 venv 内固定 entrypoint，最终形成真正的 `fresh venv → locked dependencies → observed environment → registered tool execution → ResultBundle → independent recompute` 闭环。
