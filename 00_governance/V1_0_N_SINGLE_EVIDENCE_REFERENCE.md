# V1.0-N：Paper / Presentation / Submission Single Evidence Reference

## 目标
N 不新增一套计算系统，而是切断论文、图表、SubmissionManifest 对 G/H/K 并行执行证据的旁路引用。

规范原则：
- UnifiedExecutionEvidence 是执行事实唯一规范引用；
- ResultBundle 是结果唯一规范载体；
- PaperEvidence、PresentationDataManifest、PaperManifest、SubmissionManifest 均只能通过 canonical UnifiedExecutionEvidence 追溯执行事实；
- G/H/K raw evidence 只能保留为 source_evidence，不得成为下游发布引用；
- 缺少 canonical evidence 为 NOT_RUN；
- 发现 legacy evidence 旁路引用为 FAIL；
- 不允许通过删除证据或修改 Frozen ResultBundle 让 Gate 通过。

## N 规范链
```
ResultBundle
    ↓
UnifiedExecutionEvidence
    ↓
PaperEvidence
    ↓
PresentationDataManifest
    ↓
PaperManifest
    ↓
SubmissionManifest
    ↓
Final Submission
```

## N 检查范围
1. PaperEvidence claims 必须存在 canonical UnifiedExecutionEvidence refs；
2. PresentationDataManifest、PaperManifest、SubmissionManifest 不能直接引用 legacy G/H/K evidence；
3. 各发布材料必须包含 canonical evidence 追溯关系；
4. 冲突引用必须 FAIL_CLOSED；
5. N 不重新计算模型、不修改 ResultBundle、不执行渲染。

## 兼容策略
历史材料可以读取，但进入最终提交 Gate 前必须完成 canonical evidence migration；legacy evidence 仍可留在 source_evidence 中。

## 测试要求
覆盖 canonical ref PASS、legacy ref FAIL、缺 canonical ref FAIL/NOT_RUN，以及不存在 evidence 的 NOT_RUN。
