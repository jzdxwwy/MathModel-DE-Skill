# Stage 00 — Start Skill

## 目的
建立一次数学建模项目的初始状态，并输出 `ProblemSpec`。

## 输入
- 题目文本或题目文件
- 用户要求
- 题目附件（可为目录）

## 必须完成
1. 判断 Skill Development / Benchmark / Problem Solving 模式；
2. 通过 V0.7 ingestion 读取并登记题目与附件来源；
3. 提取背景、问题、显式要求；
4. 区分已知事实、待确认信息和推断；
5. 建立 question_id；
6. 创建项目计划与 todo；
7. 对无法读取的文件明确记录，不得把“未读取”写成“无数据”。

## V0.7 输入摄取规则

确定性摄取层负责：
- 文件存在性、大小、SHA-256；
- PDF/DOCX/TXT/MD 等文本提取（可选依赖不可用时显式告警）；
- CSV/TSV/JSON/XLSX 基础结构体检；
- 附件目录展开；
- `ingestion_manifest.json` 与原始题目文本落盘。

语义理解由本 Stage 与 LLM 完成，确定性摄取层不得擅自补全题意。

## 输出
- `ProblemSpec`
- project plan
- todo
- `ingestion_manifest.json`（V0.7）

## Gate
不得把未读取、提取失败或仅由模型推断的信息写成题目事实。
