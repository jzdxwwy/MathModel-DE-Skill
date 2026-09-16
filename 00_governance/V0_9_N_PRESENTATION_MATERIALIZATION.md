# V0.9-N — Presentation Materialization / Render Pipeline

## 1. 目标

V0.9-M 解决“展示数据是否与权威结果一致”；V0.9-N 进一步解决“展示数据如何被确定性地物化并交给渲染器”。

核心原则：

> `PresentationDataManifest` 是图、表、公式生成的唯一数据源；渲染器不得重新计算、改写或猜测数值。

## 2. 标准链

`ResultBundle → PresentationDataManifest → Rendered Consistency → Materialized Presentation Payload → Render Manifest / SHA256 → Renderer → Final Artifact`

其中 V0.9-N 当前实现到 `Materialized Presentation Payload → Render Manifest / SHA256`，实际像素渲染器可以独立消费这些 payload。

## 3. Materialization Contract

每个 presentation item 必须：

1. 有唯一 `evidence_id`；
2. 通过 `bindings` 指向 `source_ref` 和 `result_ref`；
3. 能从 ResultBundle 解析出实际值；
4. 公式保留规范化表达式及 expression hash；
5. 生成确定性的 JSON payload；
6. 对 payload 计算 SHA256；
7. render manifest 记录源 PresentationDataManifest hash、run_id、payload 路径及 payload hash。

## 4. Run Isolation

多任务/多运行时，物化结果必须按 `run_id` 隔离：

- `presentation/materialized/<run_id>/...`
- `runs/<run_id>/presentation-render-manifest.json`

不得由后一个运行覆盖前一个运行的 render manifest。

Presentation item 可显式提供 `run_id`；没有 run_id 时视为通用 item。

## 5. Fail-Closed

以下情况不得进入可发布状态：

- binding 无法解析；
- ResultBundle 缺失；
- PresentationDataManifest 与结果不一致；
- payload 无法生成；
- hash 无法生成。

结果应为 `FAIL`，而不是猜测、补值或自动修改 ResultBundle。

## 6. 不负责的事情

V0.9-N 不声称完成：

- 像素级视觉质量判断；
- OCR 复核最终图片中的所有数字；
- 完整符号代数等价证明；
- Word/PDF 排版质量自动评分。

这些属于后续 Rendered Artifact / Final Submission Gate 能力。

## 7. 与 V0.9-M 的关系

V0.9-M 是一致性门：确认 manifest 中的 presentation data 与 ResultBundle 一致。

V0.9-N 是物化门：只有通过一致性检查的数据才能被确定性写入 payload，并留下 hash。

因此不能跳过 V0.9-M 直接生成 publishable presentation。
