# V1.0-V 全链路集成与缺陷收敛

## 1. 目的

V1.0-V 不新增独立 Final Gate 编号，而是验证 V1.0-A–U 已形成的证据链能否在统一运行拓扑下协同工作。

## 2. Canonical Topology

`run_dir/reference/execution/`：
- result-bundle.json
- execution.log
- unified-execution-evidence.json

`run_dir/reference/verification/`：
- verification-report.json

旧版平铺路径允许作为兼容 fallback，但新实现优先 canonical topology。

## 3. 已收敛的 schema/runtime 问题

- ResultBundle builder 补齐 `provenance.input_refs`；
- Cross-Artifact Consistency 支持 V1.0-M canonical execution/verification；
- PaperEvidence schema 正式声明 S 所需结构化公式/参数 observations；
- ModelExecutionBinding schema 与实际 gate output 字段一致；
- PaperConsistencyAudit 支持 canonical execution/verification 文件发现。

## 4. 集成测试

`tests/integration/test_v10_v_core_chain.py`

测试链：
`ResultBundle → ClaimModelTrace → ModelExecutionBinding → PaperConsistencyAudit`

并验证：
- 正常数据闭合；
- ResultBundle 数值被修改后，模型执行绑定失败；
- presentation value 与 ResultBundle 不一致时，论文一致性审计失败；
- 关键输出满足对应 JSON Schema。

## 5. 边界

该测试不等价于：
- OS/container clean-room；
- 真实依赖安装；
- 独立 rebuild；
- CUMCM D/E benchmark；
- PDF/Word OCR/视觉验收。

这些能力必须有独立的真实环境证据。

## 6. 发布判断

V 完成后，项目从“门禁堆叠”进入“集成验证与缺陷收敛”阶段。下一阶段应优先做 Final Gate 的真实全链路 fixture，而不是继续机械增加门禁编号。

## 7. 测试声明

截至本阶段提交时，仓库测试尚未实际执行；任何 PASS 均只能来自未来实际运行结果，不能由代码存在推断。
