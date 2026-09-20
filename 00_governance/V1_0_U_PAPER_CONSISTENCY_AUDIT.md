# V1.0-U：论文/图表/公式最终一致性审计

## 目标
U 审计结构化出版物工件之间的一致性：

PaperManifest ↔ PaperEvidence ↔ PresentationDataManifest ↔ ResultBundle ↔ ModelSpec

## 检查
- U01：PaperManifest claim_refs 必须解析到 PaperEvidence，且每个 material claim 必须被章节引用；
- U02：章节中的 figure/table/equation refs 必须解析到 PresentationDataManifest 且 kind 一致；
- U03：PresentationDataManifest 每个 binding 必须能解析到 ResultBundle；若声明 value，则按显式 tolerance 比较；
- U04：公式存在 expression_hash 时必须匹配；model_refs 存在时必须解析到 ModelSpec equation；
- U05：不得存在孤立的 presentation item。

## 边界
U 不 OCR PDF/Word，不从自然语言正文提取数字，不进行隐式单位换算，不做未经声明的显示精度推断，不做完整符号代数等价证明。

## 发布含义
U 通过意味着结构化论文证据、图表/公式数据清单与权威计算结果之间闭合；不等于最终 PDF/Word 的版面、OCR 文本或视觉质量已经通过。
## 测试
已加入单元测试，但尚未实际运行 pytest。
