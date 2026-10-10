# 2026 D/E 真题能力探针报告

> 本文件记录**第一次把真实竞赛题目与附件喂进 MathModel-DE-Skill** 的结果。
> 目的不是宣称能力，而是用真题定位短板。所有数字都来自实际执行。

## 1. 结论摘要

真实附件在**修复前完全读不进来**，而且链路给出的是**绿灯**。

| 检查项 | 修复前 | 修复后 |
| --- | --- | --- |
| 2026E 附件 DataProfile | `rows=0, columns=0, schema=[]`，gate=`PASS_WITH_WARNINGS` | 3 个 sheet 各自成 asset，真实行/列/表头，gate=`PASS_WITH_WARNINGS`（多表关联风险） |
| 2026D 附件 DataProfile | `rows=0, columns=0, schema=[]`，gate=`PASS_WITH_WARNINGS` | 150×5，真实表头，gate=`PASS` |
| 题目 PDF | 0 字符，仅一条"缺 pypdf"告警 | 2037 / 2178 字符，无告警 |
| 全部 tabular 都读不出时 | 仍为 `PASS_WITH_WARNINGS` | `FAIL`（schema 里本就有 `FAIL`，此前永不可达） |

## 2. 材料与年份（已核实）

题目与附件来自本地真实副本，PDF 正文首行即年份与题号：

- `2026 年高教社杯全国大学生数学建模竞赛题目 … E 题 SEM 广告投放策略`
- `2026 年高教社杯全国大学生数学建模竞赛题目 … D 题 时频冲突检测与消解`

| 材料 | 大小 | SHA256（前 16 位） |
| --- | --- | --- |
| 2026E `E题.pdf` | 342,795 B | `3E4E340AE722C5DD…` |
| 2026E `附件1.xlsx` | 313,639 B | `F6AC8E080A967194…` |
| 2026D `D题.pdf` | 442,550 B | `04945C2DB24CD6CB…` |
| 2026D `附件1.xlsx` | 16,067 B | `B7F905CD2629F9A8…` |

完整哈希记录在探针产出的 `benchmark-input-manifest.json` 中。

> ⚠️ **参考解的归属**：本地 `problem_D/`、`problem_E/` 下的 `reports/`、`code/`、`results/`、
> `figures/`、`paper/` 是**另一套 Skill（LiXiang106991/MathModelAgent）在赛期产出的**，
> 不是本项目的产物。本文仅把它当作**对照基线**用于交叉验证与定位短板；
> 不得把它当作本 Skill 的输出，也不得把其中的最终数字硬编码为"模型结果"
> （`HISTORICAL_STRESS_TEST_PLAN.md` 的既有红线）。

## 3. 缺陷与修复

### 3.1 `.xlsx` 探针契约不一致导致静默降级（最严重）

`tools/ingestion/inspectors.py::_xlsx_profile` 返回 `{"sheets": [...]}`，而
`_csv_profile` / `_json_profile` 返回 `{"rows", "columns", "columns_profile"}`。
`tools/ingestion/data_profile.py::build_data_profile` 只读后者，于是**任何 .xlsx 一律得到
0 行 0 列空 schema**；又因为 `{"sheets": ...}` 非空，`if not profile` 这条风险检查不触发，
最终既不报错也无有效告警。

**而 CUMCM 的附件就是 .xlsx**，所以这不是边角问题，是主路径完全不可用。

修复：`_xlsx_profile` 改为输出与 CSV/JSON 一致的顶层契约（`rows`/`columns`/`columns_profile`），
用 openpyxl（已是既有依赖）读取真实表头与 dtype，并保留 `sheets` 明细；openpyxl 缺失时
降级为纯标准库的行/列计数，并写入 `profile_limited` 让调用方 fail closed。

### 3.2 多 sheet 被压平，只保留第一个 sheet

2026E 的 `附件1.xlsx` 有 3 个 sheet，而 `Sheet2`（每日新注册数）、`Sheet3`（关键词统计）
正是问题二、问题四赖以建模的数据。原实现把它们整体丢弃。

修复：多 sheet 工作簿**每个 sheet 各成一个 asset**（DataProfile schema 的 `assets` 本就是数组，
无需改契约），`path_or_ref` 记录为 `<文件>#<sheet 名>`，并追加一条风险说明
"跨 sheet 关联不被推断"——关联关系必须由建模者显式声明，不由 ingestion 猜。

### 3.3 `DataProfile.gate_decision` 的 `FAIL` 永不可达

schema 允许 `PASS / PASS_WITH_WARNINGS / FAIL`，但构建器只会产生前两者。任何
"所有 tabular 附件都读不出"的情形都被记为 `PASS_WITH_WARNINGS`，即典型的 fail-open。

修复：当存在 tabular 附件且**无一**产出列 schema 时，gate 记为 `FAIL`。既有测试中
"缺 openpyxl 时告警"的期望也随之从 `PASS_WITH_WARNINGS` 修正为 `FAIL`。

### 3.4 题目 PDF 依赖未声明

`extract_text` 需要 `pypdf`，但它不在任何依赖清单里，于是**题目正文 0 字符**——
而"读题"是整个 Skill 的第一步。已加入根目录 `requirements.txt`。

### 3.5 误导性告警

`.xlsx` 会被 `extract_text` 报 "no text extractor for this format"。它本就走表格探针路径，
这条告警属于假警报，会稀释真正需要关注的告警。已停止对该格式报此告警。

## 4. 修复后的实测结果

```
===== CUMCM-2026E
  B01_INPUT_READINESS : READY  gate=NOT_RUN
  题目正文            : 2037 chars
  DataProfile gate    : PASS_WITH_WARNINGS  schema_valid=True
    asset_001_1  rows=2627   cols=10   Sheet1
    asset_001_2  rows=365    cols=2    Sheet2
    asset_001_3  rows=2227   cols=9    Sheet3
    RISK: workbook has 3 sheets; each sheet is profiled as its own asset, and cross-sheet joins are not inferred
===== CUMCM-2026D
  B01_INPUT_READINESS : READY  gate=NOT_RUN
  题目正文            : 2178 chars
  DataProfile gate    : PASS  schema_valid=True
    asset_001    rows=150    cols=5
```

各 sheet 读出的列名：

- E/Sheet1：日期, 方案ID, 推广单元ID, 展现量, 点击量, 消费额, 上方位展现量, 上方首位展现量, 上方位点击量, 上方位消费额
- E/Sheet2：日期, 新注册数
- E/Sheet3：序号, 关键词, 方案ID, 推广单元ID, 消费额, 点击量, 浏览量, 跳出率, 平均访问时长
- D/Sheet1：用频装备编号, 频段区间, 时间区间, 间隔时长, 使用次数

## 5. 与参考解的独立交叉验证

本项目的 ingestion 与参考 Skill 的产出无任何共享代码，两者对同一附件的描述必须一致：

| 数据 | MathModel-DE-Skill 读出 | 参考解 `ANALYSIS_MODELING_REPORT.md` 记录 |
| --- | --- | --- |
| E/Sheet1 | 2627 行 × 10 列 | 2627 记录 / 10 字段 ✓ |
| E/Sheet2 | 365 行 × 2 列 | 365 记录 / 2 字段 ✓ |
| E/Sheet3 | 2227 行 × 9 列 | 2227 记录 / 9 字段 ✓ |
| D | 150 个用频装备，5 列（编号 + 4 个计划参数） | "150 个用频装备"、四参数 = 频段区间/首次时间区间/间隔时长/使用次数 ✓ |

四个数据源全部吻合，说明读取结果可信。

## 6. 仍然存在的短板（按优先级）

1. **知识库几乎为空**：`knowledge/` 只有 2 个文件（3.6 KB + 5.2 KB）。参考项目有完整方法库、
   模型选择匹配库与 11 个可直接运行的 Python 实现。这是"能不能真解出题"的最大瓶颈——
   证据链再严密，也要先有能建模的东西。
2. **benchmark 仍无真实输入入库**：本次只在 `D:\0ai\_probe\` 产出了就绪证据，
   `benchmarks/` 下依然没有 2026D/2026E 的附件与基准卡。需要先决定附件是否提交进仓库。
3. **没有任何一道真题被真正求解**：`05_python/templates/` 的 11 个模板是通用模板，
   没有针对真题的 solver；`B01_INPUT_READINESS` 只检查输入齐全，`gate_decision` 恒为 `NOT_RUN`。
4. **跨 sheet 关联没有任何辅助**：目前只如实报告"不推断"。E 题问题二需要
   Sheet1 ↔ Sheet2 ↔ Sheet3 的关联，这部分工作被完整地留给了建模者。
5. **runner 层仍未完全 fail-closed**：`profile_benchmark_inputs` 新增了 `data_profile_gate`
   字段以便调用方判断，但其 `status` 仍只看 ingestion warnings。是否让"数据读不出"直接
   把 benchmark 置为 BLOCKED，需要先确定契约语义（现有测试把"附件缺失"编码为
   `READY_WITH_WARNINGS`，不能单方面改掉）。
6. **CSV 的 `PASS` 不可达**：`_csv_profile` 恒定输出 `duplicate_scope`，而 `build_data_profile`
   把它记成一条 `data_risks`，于是**任何 CSV 的 gate 都是 `PASS_WITH_WARNINGS`**。
   这条"重复检测只覆盖前 5000 行"是**已知限制**，不是数据质量问题，却被混进了风险列表，
   使最常见的格式永远拿不到 `PASS`。与 3.5 属于同一类"告警噪声淹没信号"的问题，
   需要把"限制/说明"与"风险"分开后再定契约。

## 7. 边界（不得夸大）

- 本次只验证了**输入读取**（题目文本 + 附件结构）能跑通真实真题；
  **没有**验证建模、求解、验证、论文任一环节在真题上的表现。
- `B01_INPUT_READINESS = READY` 只表示输入齐全，不表示题目已被求解。
- 2026 D/E 的参考解来自另一套 Skill，仅作对照；本项目至今**没有**产出过任何真题结果。
- 本地探针证据位于 `D:\0ai\_probe\`，尚未提交进本仓库。
