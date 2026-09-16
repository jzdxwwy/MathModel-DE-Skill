# V1.0-G Dependency Lock + Trusted Host Execution

## 目标

V1.0-G 把 V1.0-F 的“环境适配器边界”推进到可审计的执行证据层：

```text
EnvironmentClosure
→ DependencyLockManifest
→ Trusted Adapter Registry
→ Trusted Host
→ Isolated Execution
→ ExecutionEvidence
→ CleanRoomGate
→ ReproducibilityGate
```

## 1. DependencyLockManifest

锁定 Python 实现/版本、依赖包版本、工具版本/引用、源文件 SHA256，以及可选基础镜像标识。锁文件本身有确定性 fingerprint。

核心规则：
- 锁是声明性材料，不调用 pip/conda/docker。
- 未锁定的依赖不能被自动补装后视为同一次可复现运行。
- 源文件发生哈希变化时，锁验证失败。

## 2. Trusted Adapter Registry

只有显式注册且 `trusted=true` 的 adapter 才能进入 TrustedHost。核心策略禁止 shell 和网络能力；未知 adapter 或未信任 adapter 必须阻断。

adapter 的 `kind`（VENV/CONDA/DOCKER/GITHUB_ACTIONS/CUSTOM 等）只是能力分类，不代表当前运行环境已经具备该实现。

## 3. Trusted Host

Skill 本体不执行任意 shell，也不直接创建 Docker/Conda/venv。TrustedHost 是外部受控运行时的接口边界。当前仓库提供安全的校验入口；`execute()` 默认阻断，等待受信任 Host 注入真实实现。

## 4. ExecutionEvidence

真实 clean-room 运行必须产生：
- execution_status
- adapter_id / isolation_id
- dependency lock hash
- observed environment fingerprint
- tool identity
- input hashes
- execution log hash
- ResultBundle hash
- observed_at

因此“手工复制 environment-closure.json”不能单独宣称完成 clean-room execution。

## 5. Gate 语义

- 缺少执行证据：`NOT_RUN`
- 执行失败、锁/环境/日志/ResultBundle 哈希不一致：`FAIL`
- 所有证据闭合且哈希一致：`PASS`

## 6. 安全边界

V1.0-G 不允许 LLM 生成任意安装命令或 shell 命令后直接执行。实际 Docker/Conda/venv/CI 执行必须由可信 Host/Adapter 提供，并返回可验证证据。

## 7. 与 V1.0-C/D/E/F 的关系

G 不替代已有 Reproducibility、Environment Closure、Clean-Room Evidence，而是为它们提供具体的锁定材料、adapter 信任边界和执行证据。Frozen ResultBundle 永远不可被重建过程覆盖。

## 8. 当前实现限制

当前 GitHub 仓库实现的是声明性锁、adapter registry、TrustedHost 接口和证据 Gate；没有声称在 GitHub connector 内真正创建隔离环境。pytest 尚未在本次变更中执行。
