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


## 38. V1.0-M：Run Topology + Single Source of Execution Truth
V1.0-M 不再继续增加平行 execution evidence，而是进行架构收敛：统一运行目录、规范日志名称、统一 ResultBundle 构造，并把“结果身份 + 执行身份”一起纳入复现闭环。

核心链：

`RunTopology → reference/rebuild/replay → canonical execution/ → ResultBundle + execution.log → UnifiedExecutionEvidence → UnifiedReproducibilityGate`

### 38.1 Canonical Run Topology
新增：
- `artifacts/schemas/run-topology.schema.json`
- `tools/runtime/run_layout.py`

规范运行根目录：
```
<run_root>/
├── run-topology.json
├── reference/
│   ├── execution/
│   │   ├── result-bundle.json
│   │   ├── execution.log
│   │   └── unified-execution-evidence.json
│   └── verification/
├── rebuild/<rebuild_id>/
└── replay/<replay_id>/
```

M 允许读取历史 `execution-log.json`，但新执行的规范输出统一为 `execution/execution.log`。

### 38.2 ResultBundle Single Source
新增 `tools/runtime/result_bundle_builder.py`。Venv 固定 EntryPoint 不再自行维护第二套 ResultBundle 结构，而统一调用 builder。

原则：
1. ResultBundle 是计算结果的唯一规范载体；
2. execution adapter 不得定义另一套结果协议；
3. ResultBundle 不因 verification/reproducibility 结果而被修改；
4. 历史结果可以兼容读取，但新产出必须遵循 canonical schema。

### 38.3 Unified Execution Evidence
L 的 UnifiedExecutionEvidence 进一步迁移到 canonical `execution/` 目录。Unifier 会优先读取 canonical execution evidence，同时兼容历史根目录证据。

下游应只引用 UnifiedExecutionEvidence；K/G/H raw evidence 只作为 `source_evidence` 保留。

### 38.4 Unified Reproducibility Gate
新增 `tools/verification/unified_reproducibility_gate.py`。

M 同时检查：
- reference 与 rebuild 均存在 UnifiedExecutionEvidence；
- execution_status 均为 SUCCESS；
- tool_ref 一致；
- input hashes 一致；
- lock_hash 一致；
- environment_fingerprint 一致；
- ResultBundle 使用 V1.0-C `compare_result_bundles` 独立比较。

因此 M 的 PASS 不是单纯“数值相同”，而是“数值结果相同 + 执行身份闭合”。

### 38.5 Final Submission Gate
新增 F15 `UNIFIED_REPRODUCIBILITY`。当调用 Final Submission Gate 时，如果提供 rebuild_dir，则 F15 同时检查结果身份与执行身份；没有 rebuild_dir 时保持 `NOT_RUN`，不把缺证据当作 PASS。

### 38.6 安全边界
M 不增加 shell/network/arbitrary-code 权限。RunTopology、ResultBundle Builder、Evidence Unifier 与 Unified Reproducibility Gate 都是确定性文件/证据处理组件。

## 39. V1.0-M 当前状态
M 的 RunTopology schema、RunLayout、ResultBundle Builder、canonical Venv EntryPoint、canonical execution log、UnifiedExecutionEvidence 迁移、UnifiedReproducibilityGate 与 F15 已写入 GitHub。

本次会话**没有实际运行 pytest，也没有执行真实 venv 建模任务**，因此不能声称 M 已测试通过。

下一阶段应优先进入 **V1.0-N：PaperEvidence / Presentation / Submission 的 Single Evidence Reference Migration**，而不是继续无上限增加 Final Gate 编号。N 的重点是让论文、图表、表格、SubmissionManifest 全部只接受 UnifiedExecutionEvidence 作为执行事实入口，并增加冲突证据 fail-closed 规则。


## 40. V1.0-N：Paper / Presentation / Submission Single Evidence Reference
V1.0-N 的重点不是增加新的计算能力，而是切断论文与交付材料对 G/H/K 并行 execution evidence 的旁路引用。

核心链：

`ResultBundle → UnifiedExecutionEvidence → PaperEvidence → PresentationDataManifest → PaperManifest → SubmissionManifest → Final Submission`

### 40.1 Canonical Evidence Source
新增：
- `artifacts/schemas/paper-evidence-source.schema.json`
- `artifacts/schemas/submission-evidence-closure.schema.json`
- `tools/verification/paper_evidence_closure.py`
- `tools/verification/submission_evidence_closure.py`

规范：
1. ResultBundle 是结果唯一规范载体；
2. UnifiedExecutionEvidence 是执行事实唯一规范引用；
3. PaperEvidence 的 claims 必须能追溯到 canonical UnifiedExecutionEvidence；
4. Presentation、PaperManifest、SubmissionManifest 不得直接引用 G/H/K legacy evidence；
5. legacy evidence 只能作为 UnifiedExecutionEvidence 的 source_evidence 保留。

### 40.2 Fail-Closed
N 发现以下情况不允许进入 PASS：
- 缺少 UnifiedExecutionEvidence；
- PaperEvidence claim 没有 canonical execution evidence ref；
- 发布材料直接引用 execution-evidence.json、venv-tool-execution-evidence.json 或 execution-replay-result.json；
- canonical evidence 与发布材料的引用关系缺失。

N 不删除历史 evidence，也不修改 Frozen ResultBundle 来消除冲突。

### 40.3 Final Submission Gate
新增 F16：`SINGLE_EVIDENCE_REFERENCE`。

F16 的作用不是重新验证数值，而是确认“论文/图表/提交材料到底引用了哪一个执行事实源”。

### 40.4 测试与状态
新增 `tests/verification/test_v10_n_single_evidence.py`，覆盖 canonical reference PASS 和 legacy reference FAIL。

本次会话没有实际运行 pytest，因此不能声称 N 已运行通过。

N 完成后，下一阶段应重点做 **V1.0-O：Evidence Conflict Resolution + Claim-Level Lineage Closure**，把“引用了统一证据”进一步推进到“每个论文结论、数字、图表、公式都有明确 claim-level lineage，并对冲突 evidence fail-closed”。


## 41. V1.0-O：Claim-Level Lineage + Evidence Conflict Closure
V1.0-O 在 N 的 Single Evidence Reference 之上继续收敛：不只要求“引用 UnifiedExecutionEvidence”，而是要求论文中的每个可验证 Claim 都有显式 lineage，并对同一 Claim 的多来源观测进行确定性冲突检测。

核心链：

Claim → PaperEvidence → Result / Verification / Presentation → UnifiedExecutionEvidence → Input

### 41.1 Claim Lineage
新增：
- `artifacts/schemas/claim-lineage.schema.json`
- `tools/verification/claim_lineage.py`

Claim lineage 使用结构化节点和边，不使用 serialized text 搜索替代字段级关系。Claim 至少应明确：
1. claim_id；
2. statement；
3. Result / Verification / Presentation 引用；
4. UnifiedExecutionEvidence 引用；
5. 必要时的多来源 observation。

### 41.2 Evidence Conflict
新增：
- `artifacts/schemas/evidence-conflict.schema.json`
- `tools/verification/evidence_conflict.py`

确定性比较规则：
- numeric：只有 unit 相同且声明 atol/rtol 才比较；
- exact：只比较声明的 normalized_value/value；
- none：不比较；
- 单位不同、类型不同或无法确定比较关系 → NOT_COMPARABLE；
- 超出容差的数值差异 → CONFLICT；
- CONFLICT / NOT_COMPARABLE / 缺 observation → FAIL_CLOSED；
- 不允许自动选择“更可信”的来源，不做隐式单位换算。

### 41.3 Final Submission Gate
新增 F17：`CLAIM_LINEAGE_CONFLICT`。

F17 只有在：
- Claim Lineage Gate = PASS；
- Evidence Conflict Gate = PASS

时才允许 PASS。任何冲突都阻止最终提交。

### 41.4 与 N 的关系
N 解决“出版物只引用 UnifiedExecutionEvidence”；O 解决“每一个 Claim 如何沿显式图回溯，以及多个来源是否一致”。

### 41.5 测试与状态
新增 `tests/verification/test_v10_o_claim_lineage.py`，覆盖：
- 缺 canonical execution evidence → FAIL；
- canonical execution evidence → PASS；
- 数值冲突 → FAIL_CLOSED；
- 容差内一致 → PASS；
- 单位不一致 → FAIL_CLOSED。

本次会话没有实际运行 pytest，因此不能声称 O 已测试通过。


## 42. V1.0-P：Claim Evidence Index + Deterministic Claim Binding
P 不继续堆叠新的数学模型能力，而是解决 O 暴露出的工程问题：Claim 与 Result、Verification、UnifiedExecutionEvidence 之间的关系不能长期依赖人工填写。

新增：
- `artifacts/schemas/claim-evidence-index.schema.json`
- `tools/verification/claim_evidence_index.py`
- `tests/verification/test_v10_p_claim_evidence_index.py`
- `00_governance/V1_0_P_CLAIM_EVIDENCE_INDEX.md`

### 42.1 核心链
Claim → PaperEvidence → Result → Verification → UnifiedExecutionEvidence → Presentation

### 42.2 确定性抽取
P 从已有 PaperEvidence 的结构化字段抽取：
- claim_id / statement；
- result_refs；
- verification_refs；
- figure/table/equation refs；
- unified_execution_evidence_refs。

缺少 Result、Verification 或 UnifiedExecutionEvidence → FAIL_CLOSED。

### 42.3 Final Submission Gate
新增 F18：`CLAIM_EVIDENCE_INDEX`。

F18 的作用是把 O 的 Claim Lineage 从“需要显式构造”推进到“由已有 Artifact 确定性建立索引”。

### 42.4 边界
P 不重算模型、不修改 Frozen ResultBundle、不选择冲突来源、不进行隐式语义推断。

### 42.5 测试状态
已增加 P 回归测试，但本次会话没有实际运行 pytest，因此不能声称测试通过。


## 43. V1.0-Q：Claim → Entity → Verification → Execution Closure

Q 将 V1.0-P 的“引用存在”进一步升级为“引用对象真实存在、可解析、并闭合到本次执行”。

核心链：
`Claim → Result Entity → Verification Entity → ResultBundle → UnifiedExecutionEvidence`

### 43.1 Result Entity 解析
`ClaimEvidenceIndex` 中的 result ref 必须能够确定性解析：
- `output:<name>` → ResultBundle.outputs 中唯一同名输出；
- `metric:<name>` → ResultBundle.metrics 中存在该指标；
- `artifact:<path>` → ResultBundle.artifacts 中唯一同路径产物；
- `result-bundle.json` 或其路径 → 整个 ResultBundle；
- 裸名称 → 仅在 outputs 中唯一时允许。

无法解析或无法唯一确定 → FAIL_CLOSED。

### 43.2 Verification Entity 解析
verification ref 必须解析到 VerificationReport：
- `check:<check_id>` 或裸 check_id → 唯一检查项；
- 检查项必须为 PASS；
- 报告级引用必须由 VerificationReport.gate_decision 支持。

### 43.3 Execution Closure
Claim 的 UnifiedExecutionEvidence 必须满足：
- execution_status = SUCCESS；
- UE.run_id = ResultBundle.run_id；
- UE.result_bundle_hash = 实际 ResultBundle SHA256；
- Claim 引用必须指向 canonical UnifiedExecutionEvidence。

### 43.4 F19 Final Submission Gate
新增：
`F19_CLAIM_ENTITY_CLOSURE`

只有所有 Claim 都形成：
`Claim → Result → Verification → UnifiedExecutionEvidence`
闭环时，Q 才返回 PASS。

Q 不：
- 从 Claim 自然语言猜测结果；
- 自动做单位换算；
- 在冲突结果中选择一个；
- 重算模型；
- 修改 Frozen ResultBundle。

### 43.5 Q 测试
新增：
- `tests/verification/test_v10_q_claim_entity_closure.py`

覆盖：
1. 正常 Claim 实体闭环；
2. Result ref 无法解析；
3. Verification 非 PASS。

当前仓库测试尚未在本实现环境实际运行，因此不能宣称 pytest 已通过。


## 44. V1.0-R：Claim 数值级自动溯源

R 在 Q 的实体闭环基础上增加数值闭环：

`Claim observation → ClaimEvidenceIndex → ResultBundle value → tolerance comparison`

新增：
- `artifacts/schemas/claim-numeric-trace.schema.json`
- `tools/verification/claim_numeric_trace.py`
- `tests/verification/test_v10_r_claim_numeric_trace.py`
- `00_governance/V1_0_R_CLAIM_NUMERIC_TRACE.md`

新增最终门禁：
`F20_CLAIM_NUMERIC_TRACE`

### R 的重要原则
1. **不解析自然语言 Claim statement 猜数字**；
2. 数值必须来自结构化 `PaperEvidence.observations`；
3. 通过 `result_ref` 或 Claim Evidence Index 定位 ResultBundle 实体；
4. 默认比较容差 `atol=1e-8, rtol=1e-6`；
5. 两边都有单位时必须精确一致，不做隐式单位换算；
6. 缺失、非数值、超容差 → FAIL_CLOSED；
7. 不修改 ResultBundle，不重算模型，不选择冲突来源。

Q 解决“Claim 引用了哪个真实实体”；R 解决“Claim 声称的这个具体数值是否真的等于该实体中的数值”。

当前 R 单元测试已加入仓库，但尚未实际运行 pytest，因此不能宣称测试通过。


## 45. V1.0-S：公式/参数级溯源

S 在 R 的数值级溯源基础上，建立 Claim 与 ModelSpec 的结构化连接：

`Claim → ModelSpec → equation / parameter`

新增：
- `artifacts/schemas/claim-model-trace.schema.json`
- `tools/verification/claim_model_trace.py`
- `tests/verification/test_v10_s_claim_model_trace.py`
- `00_governance/V1_0_S_CLAIM_MODEL_TRACE.md`

新增最终门禁：
`F21_CLAIM_MODEL_TRACE`

### S 的确定性规则
- 公式必须来自结构化 `equation_observations`；
- 参数必须来自结构化 `parameter_observations`；
- 公式采用空白归一化后 SHA256 比较；
- 不进行“看起来等价”的代数推理；
- 参数按 symbol 唯一定位；
- 参数数值使用 atol/rtol 比较；
- 双方均有单位时必须精确一致；
- Claim.model_id 与 ModelSpec.model_id 必须一致。

S 不从论文自然语言猜公式或参数，不重算模型，不修改 ModelSpec，不选择冲突公式。

当前首版限制：单个 ModelSpec、结构化 observation、尚未做符号代数等价证明；`model-spec.json` 的标准路径后续应由运行时统一。


## 46. V1.0-T：模型—执行绑定

T 将 S 的模型结构溯源继续连接到真实执行产物：

`ModelSpec → ResultBundle → UnifiedExecutionEvidence`

新增：
- `artifacts/schemas/model-execution-binding.schema.json`
- `tools/verification/model_execution_binding.py`
- `tests/verification/test_v10_t_model_execution_binding.py`
- `00_governance/V1_0_T_MODEL_EXECUTION_BINDING.md`

新增最终门禁：
`F22_MODEL_EXECUTION_BINDING`

### T 的确定性规则
- ResultBundle.model_id = ModelSpec.model_id；
- ResultBundle.run_id = UnifiedExecutionEvidence.run_id；
- UE.result_bundle_hash = 实际 ResultBundle SHA256；
- UE.execution_status = SUCCESS；
- ModelSpec、ResultBundle、UE 必须同时存在；
- 保存 ModelSpec SHA256、ResultBundle SHA256、equation_refs、parameter_symbols。

T 只证明“模型身份与执行产物绑定”，不宣称已经证明执行代码内部进行了完整公式级重算。公式级代码等价验证留给后续阶段。


## 47. V1.0-U：论文/图表/公式最终一致性审计

U 对结构化出版物证据进行最终一致性审计：

`PaperManifest ↔ PaperEvidence ↔ PresentationDataManifest ↔ ResultBundle ↔ ModelSpec`

新增：
- `artifacts/schemas/paper-consistency-audit.schema.json`
- `tools/verification/paper_consistency_audit.py`
- `tests/verification/test_v10_u_paper_consistency.py`
- `00_governance/V1_0_U_PAPER_CONSISTENCY_AUDIT.md`

新增最终门禁：
`F23_PAPER_CONSISTENCY_AUDIT`

### U 的确定性规则
- PaperManifest 的 claim/figure/table/equation 引用必须可解析；
- PresentationDataManifest 的 binding 必须能解析到 ResultBundle；
- 声明的 presentation value 必须在显式 tolerance 内与 ResultBundle 一致；
- equation expression_hash 若存在必须一致；
- ModelSpec equation 引用若存在必须可解析；
- 不允许孤立的 presentation item。

U 不 OCR PDF/Word，不从自然语言正文猜数字，不隐式换算单位，不推断显示精度，不进行未经声明的符号等价证明。

U 通过代表“结构化论文证据链闭合”，不代表 PDF/Word 的视觉版面已经验收。


## 48. V1.0-V：全链路集成测试与缺陷收敛

V 不再新增一个孤立门禁，而是进入“集成优先、缺陷收敛”阶段。

### 48.1 V 的目标

围绕真实运行拓扑验证：
`ProblemSpec → DataProfile → ModelSpec → ResultBundle → UnifiedExecutionEvidence → ClaimEvidence → Presentation → Paper`

重点不是增加 F24，而是确认既有 F1–F23 在同一套 canonical artifact topology 下能够互相找到、互相验证。

### 48.2 本阶段已收敛的问题

1. **ResultBundle builder 与 schema 对齐**
   - `provenance.input_refs` 必须存在；
   - 统一由 `result_bundle_builder.py` 生成，避免执行入口各自构造不同 ResultBundle。

2. **V1.0-M canonical topology 与旧路径兼容**
   - Cross-Artifact Consistency 优先读取 `reference/execution/result-bundle.json`；
   - Verification 优先读取 `reference/verification/verification-report.json`；
   - Presentation/Paper 仍保留旧路径 fallback。

3. **S 的结构化输入正式进入 PaperEvidence schema**
   - `equation_observations`
   - `parameter_observations`
   
   因而 S 不再依赖“schema 外字段”。

4. **T 的 schema 与实际输出一致**
   - 增加 `gate_decision`
   - 增加 `violations`

5. **U 支持 canonical execution/verification 路径**
   - 避免结构化一致性审计因路径差异误报 NOT_RUN。

### 48.3 V 核心集成 Smoke Test

新增：
`tests/integration/test_v10_v_core_chain.py`

覆盖：
- ResultBundle builder；
- ResultBundle schema validation；
- Claim → ModelSpec 公式/参数溯源；
- ModelSpec → ResultBundle → UE 绑定；
- Paper/Presentation → ResultBundle 一致性；
- 对 ResultBundle 注入数值篡改后，T/U 必须 FAIL。

该测试不伪装成完整 clean-room/rebuild 测试；外部执行环境证据仍由 G–M 负责。

### 48.4 V 的原则

> **先让已有链路在同一拓扑中真正跑通，再考虑增加新能力。**

V 阶段禁止为了“看起来更完整”继续无限增加门禁。后续重点转向：
- 全 Final Gate 集成；
- 真实 D/E benchmark；
- clean-room / rebuild；
- Paper/PDF/Word materialization；
- 性能与失败恢复；
- 发布打包。

### 48.5 测试状态

V 已增加核心集成测试，但本次会话仍未在仓库运行环境中实际执行 pytest，因此当前只能称为“代码级集成测试已建立”，不能声称测试通过。
