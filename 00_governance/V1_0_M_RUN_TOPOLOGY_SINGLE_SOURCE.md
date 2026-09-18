# V1.0-M：Run Topology + Single Source of Execution Truth

## 目标
M 不再继续堆叠独立执行证据，而是统一运行目录、日志命名、ResultBundle 产出和执行证据引用。

## 规范拓扑
一个任务运行根目录统一为：
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

旧的 `execution-log.json` 只能作为兼容输入，不再作为规范输出；规范输出是 `execution.log`。

## Single Source of Truth
1. ResultBundle 是计算结果的唯一规范载体；执行器不得重新定义另一套结果结构。
2. UnifiedExecutionEvidence 是执行事实的唯一规范引用；G/H/K 原始证据可保留，但下游不得把它们当作最终执行事实。
3. Presentation、PaperEvidence、SubmissionManifest、Final Gate 应引用 canonical evidence，而不是并行证据文件。
4. 任何冲突不得通过猜测合并；应 FAIL_CLOSED。

## 可复现性闭环
M 的复现门同时检查：
- reference/rebuild 均有 UnifiedExecutionEvidence；
- tool、输入哈希、lock_hash、environment_fingerprint 一致；
- 两次 execution_status 均 SUCCESS；
- ResultBundle 经 V1.0-C 独立比较一致。

因此，“结果一样”与“执行身份一样”同时成立才算 PASS。

## 兼容与迁移
M 允许读取历史目录中的旧文件，但新执行必须写 canonical 路径。
迁移期间不得修改 Frozen ResultBundle 来迁就证据。

## 安全边界
M 不扩大 shell、network 或任意代码执行权限。它只是路径和证据拓扑规范化。

## 测试要求
至少覆盖：
- topology path resolution；
- canonical log path；
- ResultBundle 单一产出；
- reference/rebuild evidence closure；
- tool/lock/environment/input identity mismatch；
- result mismatch；
- legacy `execution-log.json` 不被当作 canonical 输出。
