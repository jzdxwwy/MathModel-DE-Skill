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
- 06 Verification：通用核验 + Domain Rule Registry + Mathematical Acceptance + Independent Recompute + Evidence Lineage + Rendered Consistency + Presentation Materialization + Reproducibility + Environment Closure + Clean-Room Evidence → VerificationReport
- 07 Writing：PaperEvidence Gate 与 Presentation Gate 通过后才允许冻结证据并写论文；PaperManifest 规定论文结构与证据映射
- 08 Final Submission：Final Submission Gate 汇总验证、展示物化、论文、环境闭包、Clean-Room Evidence 与交付文件，决定最终是否允许标记提交完成

## 3. D/E 定位
D/E 是先验，不是固定模板。先识别 prediction、evaluation、optimization、classification、clustering、simulation、mechanism、network、risk、comprehensive_decision 等任务类型，再结合 D/E 知识缩小模型空间。

## 4. Runtime / Gate
`Input Boundary → ProblemSpec → ProblemMap → DataProfile → ModelPlan → ModelSpec → Deterministic Binding → ToolDispatch → ToolRegistry → Numerical Adapter → ResultBundle → Domain Rule Registry → Mathematical Acceptance → Independent Recompute → Evidence Lineage → PaperEvidence → Presentation Evidence → Rendered Consistency → Presentation Materialization → Render Manifest → PaperManifest → SubmissionManifest → Cross-Artifact Consistency → Environment Closure → Environment Adapter → Clean-Room Execution Evidence → Reproducibility Gate → Writing → Final Submission Gate`

Gate：`Analysis → Data → Model → Binding → Compute → Verification → PaperEvidence → Presentation → RenderedConsistency → Materialization → EnvironmentClosure → EnvironmentAdapter → CleanRoomEvidence → Reproducibility → CrossArtifactConsistency → Writing → FinalSubmission`。任何关键 Gate 未通过不得标记完成。

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

## 24. V1.0-F：Environment Adapter / Dependency Lock / Clean-Room Execution Evidence
V1.0-F 把 V1.0-E 的“环境记录与比较”推进到可插拔的执行边界。

核心链：
`EnvironmentClosure → EnvironmentAdapterContract → Trusted Host Adapter → Isolated Execution → Observed EnvironmentClosure → CleanRoomGate → ReproducibilityGate`

新增：
- `artifacts/schemas/environment-adapter.schema.json`
- `tools/runtime/environment_adapter.py`
- `tools/verification/clean_room_gate.py`
- `tests/verification/test_v10_f_environment_adapter.py`
- `00_governance/V1_0_F_CLEAN_ROOM_EXECUTION.md`

### EnvironmentAdapter
适配器类型抽象为：`HOST`、`VENV`、`CONDA`、`DOCKER`、`GITHUB_ACTIONS`、`CUSTOM`。这些类型不代表当前 Runtime 已经拥有对应环境。真正的隔离创建与执行必须由受信任 Host 实现，Skill 不把模型生成字符串转换为 shell 命令。

### Dependency Lock
V1.0-F 要求 adapter 能把依赖版本、解释器版本、tool/source hash、完整 input hash 纳入 EnvironmentClosure。具体实现可以使用 requirements lock、Conda lock、container digest 或 CI runner fingerprint，核心层不硬编码某一种技术。

### Clean-Room Execution Evidence
CleanRoomGate 比较 reference/rebuild 的 Python、platform、packages、tools、source_files、inputs、model_refs、spec_refs 与 policy。缺失 rebuild evidence → `NOT_RUN`；明确环境差异 → `FAIL`；完整一致 → `PASS`。

### 安全边界
- adapter contract 不允许 arbitrary shell；
- 默认 `allow_network=false`；
- adapter 是执行能力声明，不是执行已经发生的证明；
- 只有受信任 Host 返回的 `REBUILD_OBSERVED` EnvironmentClosure 才能作为真实 clean-room evidence；
- Frozen ResultBundle 与 reference EnvironmentClosure 不可被重建修改；
- GitHub 文件写入成功不等于真实 clean-room execution 已经发生。

## 25. 当前测试状态
V1.0-F 的代码、Schema、治理规范与回归测试已写入 GitHub。当前会话没有在真实 Runtime 中执行 pytest，也没有创建 Docker/Conda/venv 隔离环境，因此不能声称 V1.0-C/D/E/F 测试或真实 clean-room execution 已通过。

## 26. 下一阶段
V1.0-G 应进入 **Dependency Lock Materialization + Trusted Host Execution**：生成标准化 lock manifest，建立 adapter registry，将 Docker/venv/Conda/CI 等具体 adapter 接入受信任 Host，并记录 execution log、environment fingerprint、command identity、input hashes 与 rebuilt ResultBundle 的闭包关系。届时才具备“真正自动 clean-room rebuild”的运行时基础。
