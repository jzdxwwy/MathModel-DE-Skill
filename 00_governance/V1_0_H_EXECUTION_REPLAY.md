# V1.0-H：Real Host Adapter Materialization + Execution Replay

## 目标

V1.0-H 把 V1.0-G 的“可信 Host 执行边界”推进到可实际回放的受控执行路径：

`ExecutionReplayContract → Trusted Adapter → Registered Tool → Input Hash Check → Tool Execution → ResultBundle → Execution Log → Hash-linked Evidence → Replay Gate`

## 核心原则

1. 核心 Skill 不执行 arbitrary shell。
2. 只能调用 ToolRegistry 中已注册的工具。
3. Adapter 必须在 AdapterRegistry 中显式 trusted，且满足 isolation=true、shell=false、network=false。
4. 执行前必须验证声明的输入文件 SHA256。
5. 可选的 dependency lock hash 和 environment fingerprint 若在 contract 中声明，则执行时必须精确匹配。
6. reference ResultBundle 不覆盖；replay 始终写入新的 run/output 目录。
7. ExecutionEvidence 必须同时绑定 adapter、isolation、tool、input hashes、lock hash、environment fingerprint、execution log hash、ResultBundle hash。
8. Evidence hash 不等于安全证明；真实 Docker/Conda/venv 隔离仍由受信任 Host 的具体实现负责。

## 当前实现

`tools/runtime/execution_replay.py` 提供受控回放引擎。它通过 ToolRegistry 调用已注册 callable，而不是解释模型生成的命令字符串，因此可以在核心 Runtime 中安全验证闭包关系。

当前版本没有在 GitHub 操作中启动 Docker/Conda/venv，也不伪装成已经完成 OS 级隔离。真实 Host 可以在同一契约下实现具体 adapter，然后回传观察到的环境与执行证据。

## Gate

`execution_replay_gate.py` 检查：
- EXECUTED 状态；
- ResultBundle 存在且 SHA256 与证据一致；
- execution log 存在且 SHA256 一致；
- adapter/tool/isolation identity；
- dependency lock hash；
- environment fingerprint。

缺少证据为 `NOT_RUN`；哈希或身份不一致为 `FAIL`；闭包完整为 `PASS`。

## 下一阶段

V1.0-I 应实现具体 Host Adapter Materialization：在受信任执行机上根据 lock manifest 创建隔离环境，并采集真实 package inventory、interpreter identity、container/venv identity、开始/结束时间、命令/工具身份和完整日志；随后将观察到的 EnvironmentClosure 与 replay ResultBundle 自动送入 V1.0-C Reproducibility Gate。
