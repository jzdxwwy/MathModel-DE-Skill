# V0.9 — Compute Execution

## 目标

把 V0.8 的 `ToolDispatchPlan` 从“计划”推进到真实的可审计执行边界，形成：

```text
ToolDispatchPlan
→ ToolRegistry
→ ToolExecutionEngine
→ RunManifest
→ ResultBundle
```

## 核心规则

1. 只能执行已经注册的 ToolRegistry 工具。
2. 工具名不能由模型运行时随意注入。
3. 每次执行生成唯一 `run_id`。
4. 执行前写入 `RUNNING` RunManifest。
5. 成功必须写 `RUN_COMPLETE`；异常必须写 `FAILED`。
6. ResultBundle 必须记录 run_id、task_id、model_id、tool。
7. 不把“工具被调用”当成“数学结果正确”。正确性留给 Verification Stage。
8. V0.9 不负责论文生成，也不负责最终质量判定。

## 当前实现边界

V0.9 已建立通用执行引擎和默认工具适配器，但默认适配器当前主要验证“dispatch → tool → manifest/result”的运行链路，不虚构具体数学计算结果。

后续应逐个把已有 Python 模板接入 ToolRegistry，并为每类模型增加真实输入适配、结果 Schema、数值验证和 smoke/regression test。
