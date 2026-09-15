# V0.7-B：结构化 Artifact 自动生成

## 目标

把 V0.7 的：

```text
题目/附件 → 确定性摄取 → LLM
```

升级为：

```text
题目/附件
→ 确定性摄取
→ LLM 语义提议
→ Artifact 标准化
→ JSON Schema Gate
→ 跨 Artifact Gate
→ 持久化
```

## 三个前端 Artifact

| Stage | Artifact | 权威事实 | LLM职责 | Gate |
|---|---|---|---|---|
| 00 | ProblemSpec | 题目原文、附件清单 | 题目标题、模式、问题拆分 | Schema + 必填字段 |
| 01 | ProblemMap | ProblemSpec.task_id | 目标、输入、输出、依赖、风险 | Schema + task_id 对齐 |
| 02 | DataProfile | ingestion/data_profile | 数据风险、预处理语义判断 | Schema + 确定性资产事实不可覆盖 |

## LLM 输出协议

优先接受直接 Artifact JSON；也兼容：

```json
{
  "artifact_type": "ProblemSpec",
  "artifact": { }
}
```

当前 Runtime 要求模型尽量只返回 JSON，不把 Markdown、解释文字混入 Artifact。

## 权威性原则

### ProblemSpec

LLM 可以组织题目语义，但不得补造题目没有提供的数据、参数或约束。

### ProblemMap

ProblemSpec 是上游事实源。ProblemMap 必须覆盖每个 `task_id`，不能自行新增未确认的任务。

### DataProfile

确定性摄取结果优先级最高。以下字段不得由 LLM 覆写：

- 文件路径/引用
- 文件格式
- 字节数
- 行列规模
- 已检测 schema
- 已检测缺失/重复事实

LLM 只能补充：

- data_risks
- 语义上的数据关系/风险判断（当前 Schema 支持范围内）
- gate_decision 建议

最终 `gate_decision` 由确定性风险与 LLM 建议共同决定，不能因为 LLM 返回 PASS 就消除确定性摄取警告。

## 失败策略

Artifact 不通过 Schema 或跨 Artifact Gate：

```text
artifact.status = DRAFT
→ 当前 Stage FAIL
→ Runtime 不进入下一 Stage
```

不得把“LLM 返回了一个看起来完整的 JSON”当作成功。

## 审计

原始模型输出保留在：

```text
runtime/00-start.json
runtime/01-analysis.json
runtime/02-data.json
```

标准 Artifact 保留在：

```text
artifacts/problem-spec.json
artifacts/problem-map.json
artifacts/data-profile.json
```

这样可以同时追踪：

```text
LLM 原始输出 → 标准化 Artifact → Gate 结果
```

## 当前限制

V0.7-B 只完成前端三个 Artifact 的自动生成与门禁，不代表已经完成数学建模。下一阶段必须利用这些 Artifact 驱动模型候选、模型比较、ModelPlan/ModelSpec、Tool Dispatch 和计算。
