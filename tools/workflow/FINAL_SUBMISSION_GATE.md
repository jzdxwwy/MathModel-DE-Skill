# V0 Final Submission Gate

本 Gate 用于判断一次端到端运行是否可以标记为“可交付”。

## 必须满足

- [ ] ProblemSpec 存在
- [ ] ProblemMap 存在且覆盖全部问题
- [ ] DataProfile 存在，数据来源与处理可说明
- [ ] ModelPlan + ModelSpec 存在
- [ ] RunManifest + ResultBundle 存在
- [ ] 图表/表格证据存在且来自结果
- [ ] VerificationReport 存在且无关键 FAIL
- [ ] PaperEvidence 存在
- [ ] 论文存在
- [ ] 核心数字在结果、验证和论文之间一致
- [ ] 核心结论能够反向追溯到结果、运行、模型和输入

## V0 与生产版的区别

V0 只保证“流水线能跑通”和“证据链接口存在”，不声称已经具备国赛 D/E 全模型覆盖能力，也不声称论文已经达到最终竞赛排版质量。

后续版本逐项替换：

1. demo Stage runner → 真实题目理解/数据处理/建模/计算 Stage；
2. placeholder figure → 真实绘图工具；
3. Markdown paper → DOCX/PDF 标准模板；
4. schema gate → semantic/lineage/reproducibility gate；
5. synthetic benchmark → 2024/2025 D/E regression benchmark。
