# V0.9-N — Reproducible Presentation / Submission Pipeline

## 1. 目标

V0.9-M 解决“展示数据是否与权威结果一致”；V0.9-N 将其升级为可重建交付链：展示数据确定性物化、渲染输入留痕、论文结构证据映射，以及运行级 SubmissionManifest。

核心原则：

> `PresentationDataManifest` 是图、表、公式生成的唯一数据源；`PaperManifest` 是论文结构与证据引用的唯一映射；`SubmissionManifest` 是一次运行的可复现交付索引。

目标不是“自动生成漂亮图片”，而是让任何 publishable artifact 都能回答：它来自哪个 run、哪个 ResultBundle、哪些 evidence，以及哪个确定性 payload。

## 2. 标准链

`ResultBundle → PresentationDataManifest → Rendered Consistency → Materialized Presentation Payload → Render Manifest / SHA256 → Renderer → PaperManifest → Paper → SubmissionManifest`

当前 V0.9-N 已实现：

- PresentationDataManifest → Materialized Presentation Payload；
- payload SHA256 与 render-input SHA256；
- PresentationRenderManifest；
- PaperManifest builder/schema；
- SubmissionManifest builder/schema；
- verification_engine 自动写入运行级 SubmissionManifest。

实际像素渲染器、Word/PDF 排版和最终提交压缩包仍由后续 Final Submission Gate 完成。

## 3. Presentation Materialization Contract

每个 presentation item 必须：

1. 有唯一 `evidence_id`；
2. 通过 `bindings` 指向 `source_ref` 和 `result_ref`；
3. 能从 ResultBundle 解析实际值；
4. 公式保留规范化表达式及 expression hash；
5. 生成确定性的 JSON payload；
6. payload 记录 `source_manifest_sha256` 与 `result_sha256`；
7. 对 payload 计算 SHA256；
8. render manifest 记录源 manifest、run、result hash、payload 路径和 payload hash。

物化器不得重新计算模型结果、修改 ResultBundle、猜测缺失字段。

## 4. PaperManifest Contract

`PaperManifest` 不生成论文正文，只规定论文结构与证据关系。

每个 section 至少需要：

- `section_id`；
- `title`；
- `claim_refs`；

并可显式绑定 `figure_refs`、`table_refs`、`equation_refs`、`render_refs`。

因此后续 Writing 阶段必须从已经通过 PaperEvidence Gate 的 claim 和已经物化的 presentation artifact 生成正文，而不是自行创造数字或引用。

## 5. SubmissionManifest Contract

`SubmissionManifest` 是一次 run 的可复现索引，不替代 Final Gate。

它记录：

- `run_id`；
- problem / attachment hash（若上游提供）；
- Git commit（若环境提供）；
- Python / platform 环境；
- 已存在交付 artifact 的相对路径及 SHA256；
- PaperManifest、PresentationDataManifest、RenderManifest、VerificationReport 引用；
- 当前 gate decision。

如果显式要求纳入的 artifact 不存在，manifest 必须 `FAIL`；不得把缺失文件伪装成已交付。

## 6. Run Isolation

多任务/多运行时必须按 `run_id` 隔离：

- `presentation/materialized/<run_id>/...`
- `runs/<run_id>/presentation-render-manifest.json`
- `runs/<run_id>/submission-manifest.json`

不得由后一个运行覆盖前一个运行的 render/submission manifest。

## 7. Fail-Closed

以下情况不得进入可发布状态：

- binding 无法解析；
- ResultBundle 缺失；
- PresentationDataManifest 与结果不一致；
- payload 无法生成；
- payload hash 无法生成；
- 显式声明的 Submission artifact 缺失。

结果应为 `FAIL`，而不是猜测、补值或自动修改权威结果。

## 8. 不负责的事情

V0.9-N 不声称完成：

- 像素级视觉质量判断；
- OCR 复核最终图片中的所有数字；
- 完整符号代数等价证明；
- Word/PDF 排版质量自动评分；
- 最终 ZIP/提交文件完整性验收。

这些属于 V1.0 Final Submission Gate。

## 9. 与 V0.9-M 的关系

V0.9-M：一致性门，确认 presentation data 与 ResultBundle 一致。

V0.9-N：物化与可复现门，只有通过一致性检查的数据才能确定性写入 payload，并留下可验证 hash；同时建立 PaperManifest 与 SubmissionManifest。

因此：

`M PASS → N Materialization → Render Manifest → Paper Manifest → Submission Manifest`

不能跳过 M 直接生成 publishable presentation。
