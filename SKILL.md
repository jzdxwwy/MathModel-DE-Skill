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


## 31. V1.0-J：Locked Dependency Installation + Observed Environment Inventory
V1.0-J 把 V1.0-I 的“venv 已创建”推进到“依赖闭包已经实际安装，并由目标解释器反向盘点”。核心链：

`DependencyLockManifest → DependencyMaterializationContract → Fresh venv → Fixed-Argv Installer → Local Wheelhouse → EnvironmentInventory → DependencyMaterializationEvidence → DependencyMaterializationGate`

### 31.1 DependencyMaterializationContract
新增 `artifacts/schemas/dependency-materialization-contract.schema.json`，冻结：
- venv 解释器；
- DependencyLock fingerprint；
- 精确 package name/version；
- 可选 package SHA256；
- local wheelhouse；
- `allow_network=false`；
- `allow_shell=false`；
- `require_hashes`。

### 31.2 Fixed-Argv Installer
新增 `tools/runtime/dependency_installer.py`。

安装器只允许受信任 Host 调用固定参数向量：
`venv-python -m ensurepip --upgrade` → `venv-python -m pip install --no-index ...`。

使用 `subprocess.run(..., shell=False)`，不接受模型生成的命令字符串；网络关闭时，非空依赖集合必须提供 local wheelhouse。package name/version 在进入 argv 前进行白名单格式校验。

如果 `require_hashes=true`，每个锁定 package 必须带 SHA256，并通过 pip `--require-hashes` 强制校验。

### 31.3 Observed Environment Inventory
新增 `tools/runtime/environment_inventory.py` 与 `artifacts/schemas/environment-inventory.schema.json`。

盘点必须由**目标 venv 自身解释器**执行，使用 `importlib.metadata` 获取实际安装 package/version，排序后生成 fingerprint。这样不是“相信 lock”，而是“观察实际环境”。

### 31.4 Dependency Materialization Evidence / Gate
新增：
- `artifacts/schemas/dependency-materialization-evidence.schema.json`；
- `tools/verification/dependency_materialization_gate.py`。

Gate 对每个 lock package 做精确 version 比对，并验证 lock hash、inventory fingerprint、interpreter identity。缺少证据为 `NOT_RUN`，安装失败或实际环境与 lock 不一致为 `FAIL`。

### 31.5 Final Submission Gate
新增 F12：`DEPENDENCY_MATERIALIZATION`。

最终环境链现在进一步成为：
`F11 Host Materialization → F12 Locked Dependency Materialization → F10 Execution Replay → Reproducibility`。

F12 不意味着模型工具已经在 venv 中运行；它只证明声明的依赖环境已经被受控安装并被目标解释器观察到。

## 32. V1.0-J 安全边界
- 不允许 LLM 生成 pip/shell 命令；
- shell/network 默认关闭；
- 默认使用 local wheelhouse，不从公网解析依赖；
- package name/version/hash 在执行前校验；
- reference ResultBundle 不参与覆盖或修改；
- EnvironmentInventory 必须来自目标 venv interpreter；
- venv 仍不是 OS/container 安全边界；
- J 仍不执行建模 ToolRegistry callable，跨进程建模执行留给下一阶段。

## 33. V1.0-J 当前测试状态与下一阶段
V1.0-J 的 Schema、固定参数安装器、EnvironmentInventory、DependencyMaterializationEvidence、Gate、F12 与回归测试已写入 GitHub。本次会话**没有实际运行 pytest，也没有在真实执行机安装依赖**，因此不能声称 J 已运行通过。

下一阶段进入 V1.0-K：将一个已注册建模工具绑定到**固定的 venv module entrypoint**，在目标 venv 中真正执行，并把 ResultBundle、Execution Log、Observed EnvironmentClosure、ExecutionEvidence、V1.0-C Reproducibility 自动闭环起来。核心 Skill 仍禁止 arbitrary shell。


## 34. V1.0-K：Venv Tool Execution
V1.0-K 首次把“依赖环境已经物化”推进到“已注册建模工具真正运行在目标 venv 进程中”。核心链：

VenvToolExecutionContract → input hash verification → trusted module resolver → target venv Python → registered ToolRegistry id → ResultBundle → execution log → VenvToolExecutionEvidence → VenvToolExecutionGate。

新增：
- artifacts/schemas/venv-tool-execution-contract.schema.json
- artifacts/schemas/venv-tool-execution-evidence.schema.json
- tools/runtime/venv_tool_executor.py
- tools/runtime/venv_tool_entrypoint.py
- tools/verification/venv_tool_execution_gate.py
- tests/verification/test_v10_k_venv_execution.py
- 00_governance/V1_0_K_VENV_TOOL_EXECUTION.md

### 34.1 固定 EntryPoint
Host 只允许调用固定 Python module，并通过显式 argv 传递已验证的 tool id、payload path、output path。模型不能提供 Python source、-c code、shell syntax 或任意 import path。

### 34.2 Evidence
K 证据闭合 run_id、adapter_id、tool、interpreter、isolation_id、input hashes、DependencyLock hash、observed environment fingerprint、ResultBundle hash 与 execution log hash。

### 34.3 Final Submission Gate
新增 F13 VENV_TOOL_EXECUTION。现在最终执行链已经达到：
Fresh venv → Locked Dependencies → Observed Environment → Registered Tool → Venv Process → ResultBundle。

### 34.4 边界
K 只证明工具已经在目标 venv 进程中运行；它尚未把 K 的结果自动接入既有 ExecutionEvidence、ExecutionReplay 与 V1.0-C Reproducibility Gate。该闭环留给 V1.0-L。

## 35. V1.0-K 当前状态
K 的 Contract、Evidence、固定 EntryPoint、Venv Executor、Gate、F13 与回归测试已写入 GitHub。本次会话没有实际运行 pytest，也没有在真实 venv 中执行完整建模工具，因此不能声称 K 已运行通过。特别是目标 venv 是否包含某个具体建模工具所需的第三方依赖，必须由 J 的 locked dependency materialization 先行保证。

下一阶段 V1.0-L：统一 K 的 ResultBundle / Execution Log / Evidence 与 G/H/C 现有证据链，消除重复 ResultBundle 构造，并让 K 的实际 venv execution 自动进入 Reproducibility comparison。


## 36. V1.0-L：Evidence Unification + Reproducibility Closure
V1.0-L 解决 K 与既有 G/H/C 证据链并行的问题。核心链：

K ResultBundle + K Execution Log + G/H/K raw evidence → UnifiedExecutionEvidence → EvidenceUnificationGate → V1.0-C compare_result_bundles → ReproducibilityClosureReport。

新增：
- artifacts/schemas/unified-execution-evidence.schema.json
- tools/verification/execution_evidence_unifier.py
- tools/verification/evidence_unification_gate.py
- tools/verification/reproducibility_closure.py
- tests/verification/test_v10_l_evidence.py
- 00_governance/V1_0_L_EVIDENCE_UNIFICATION.md

### 36.1 Canonical Evidence
UnifiedExecutionEvidence 是下游 PaperEvidence、SubmissionManifest 和 Final Submission 应引用的统一执行证据。G/H/K 原始 evidence 不删除，保留为 source_evidence。

### 36.2 Hash Closure
L 不执行代码、不重新计算模型、不修改 ResultBundle。ResultBundle 与 execution-log 的 SHA256 均从实际文件重新计算；lock/environment/tool/interpreter/isolation/input 等身份来自已有执行证据。

### 36.3 Reproducibility Closure
L 复用 V1.0-C 的 compare_result_bundles，沿用 atol=1e-8、rtol=1e-6，不重新发明比较规则。reference 与 rebuild 的 ResultBundle 只有在现有比较契约下完全一致才允许 PASS。

### 36.4 Final Submission Gate
新增 F14 EVIDENCE_UNIFICATION。Final Submission Gate 在发现 K execution evidence 时自动尝试生成 UnifiedExecutionEvidence，然后进行统一证据 Gate 检查。

## 37. V1.0-L 当前状态
L 的 canonical schema、unifier、gate、reproducibility closure、回归测试与 F14 已写入 GitHub。本次会话仍**没有实际运行 pytest**，因此不能声称 L 已测试通过。下一阶段 V1.0-M 应继续解决 run-directory topology、统一 execution.log/result-bundle 的单一来源，并让 UnifiedExecutionEvidence 成为 PaperEvidence、SubmissionManifest 与最终交付的唯一执行证据引用。
