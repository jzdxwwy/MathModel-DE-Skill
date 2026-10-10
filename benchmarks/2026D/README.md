# 2026D：时频冲突检测与消解

> Benchmark ID `CUMCM-2026D`　类型 D（组合优化／机理类）
> 状态 **B01_INPUT_READINESS = BLOCKED（附件 2 缺失）**

## 1. 题目

2026 年高教社杯全国大学生数学建模竞赛 D 题。某区域内大量用频装备对有限带宽频率资源提报用频计划，
需检测潜在的时频冲突并加以消解。

题目约定：

- 时域以固定时间长度 Δ*t* 为最小不可拆分单位，用频时间长度必须是 Δ*t* 的整数倍；
- 频域以固定带宽 Δ*f* 离散化为 **100 个**宽度相同的频段，每个计划占用连续多个频段且数量不变；
- 每个用频计划含四个参数：**频段区间**、**首次使用的时间区间**、**相邻两次使用的间隔时长**、**使用次数**；
- 当两个计划的时间区间与频段区间**都存在交叠**时判为时频冲突；
- 消解手段是调整参数或撤销计划，**一个用频计划只能调整其中一个参数或撤销**；
- 除非特别说明，一般不调整使用次数和间隔时长；应尽可能减少撤销、尽量减少被调整的计划数量；
- 优先级 A 类最高、B 类其次、C 类最低，高优先级计划应尽量保持；
- 频段、时间的最大平移幅度分别为 **10Δ*f*** 和 **5Δ*t***。

## 2. 子问题（依据题目原文提炼，非引自任何参考解）

1. **时频冲突检测**：对附件 1 的用频计划做冲突检测，冲突对写入 `result1.xlsx`，并在论文中给出统计结果。
2. **冲突消解（受限平移）**：在平移幅度限制（频段 ≤10Δ*f*、时间 ≤5Δ*t*）下消解冲突，
   方案写入 `result2.xlsx`，并按题目表 1 给出 A/B/C 三类的保留、调整、撤销统计。
3. **容量上限（不限平移）**：基于问题 2 得到的无冲突计划，若不限制平移幅度、且不增加时频资源，
   **最多还能安排多少 C 类用频装备**，给出相应计划并写入 `result3.xlsx`。
4. **可调间隔的消解**：若允许部分 C 类装备调整间隔时长（与原间隔差异不超过 10Δ*t*），
   重新对问题 1 检测出的冲突做消解，写入 `result4.xlsx`，并按表 1 给出统计。

## 3. 输入清单

| attachment_id | 文件 | 大小 | 状态 | SHA256 |
| --- | --- | --- | --- | --- |
| `problem_statement` | `inputs/D题.pdf` | 442,550 B | PRESENT | `04945c2db24cd6cb659de55e6a23ddd43553ec61bc1c7741010a7eac220712a9` |
| `attachment_1` | `inputs/附件1.xlsx` | 16,067 B | PRESENT | `b7f905cd2629f9a85b47db352be503404a0cd5b8f70b9209aafdf7e262f3449c` |
| `attachment_2_result1` | `inputs/附件2/result1.xlsx` | — | **MISSING** | — |
| `attachment_2_result2` | `inputs/附件2/result2.xlsx` | — | **MISSING** | — |
| `attachment_2_result3` | `inputs/附件2/result3.xlsx` | — | **MISSING** | — |
| `attachment_2_result4` | `inputs/附件2/result4.xlsx` | — | **MISSING** | — |

## 4. 数据结构（由本项目 ingestion 实际读出）

`inputs/附件1.xlsx`：1 张表单，**150 行 × 5 列**——

| asset | sheet | 行 | 列 | 列名 |
| --- | --- | --- | --- | --- |
| `asset_001` | Sheet1 | 150 | 5 | 用频装备编号, 频段区间, 时间区间, 间隔时长, 使用次数 |

150 与题目所述"A、B、C 三类共 150 个用频装备"一致；5 列 = 装备编号 + 四个计划参数，与题目附录一致。
该行数列名已与另一套完全独立的 Skill 在赛期产出的分析报告比对吻合，详见 `../CAPABILITY_PROBE_2026DE.md`。

## 5. 结果模板（附件 2）列为题目附录所述

| 文件 | 列 |
| --- | --- |
| `result1.xlsx` | 序号, 冲突装备1, 冲突设备2 |
| `result2.xlsx` | 用频装备编号, 调整后频段区间, 调整后时间区间, 是否撤销用频计划 |
| `result3.xlsx` | 新增用频装备序号, 调整后频段区间, 调整后时间区间 |
| `result4.xlsx` | 用频装备编号, 调整后频段范围, 调整后时间区间, 调整后间隔时长, 是否撤销用频计划 |

## 6. 为什么当前是 BLOCKED

题目要求结果"保存到文件 result*.xlsx（模板文件见附件 2）"，因此 **附件 2 的 4 个模板是本 benchmark
的必需输入**。本地工作区里与 result*.xlsx 同名同结构的文件**只有参考解填好的结果**
（`problem_D/results/result1.xlsx` 有 238 组冲突对，`result2/4.xlsx` 各 114 条调整），
**不存在任何空白模板**：

| 候选文件 | 非空行 | 判定 |
| --- | --- | --- |
| `problem_D/results/result1.xlsx` | 238 | 参考解**输出**，不是模板 |
| `problem_D/results/result2.xlsx` | 114 | 参考解**输出**，不是模板 |
| `problem_D/results/result3.xlsx` | 90 | 参考解**输出**，不是模板 |
| `problem_D/results/result4.xlsx` | 114 | 参考解**输出**，不是模板 |

把参考解的输出改个名字当模板塞进来，等于**伪造 benchmark 输入**——这正是本项目要防的事。
所以这 4 个模板被显式声明为 `required` 且当前 `MISSING`，让就绪检查 **fail closed**。

**补全方式（需人工确认来源）**：拿到官方附件 2 的空白模板后放入 `inputs/附件2/`，
再重跑下面的命令即可转 READY。题目附录已完整描述每张表的列含义，但**由我们自己照附录造模板
属于构造输入**，必须先经确认并在文档中标注来源，不得默默进行。

## 7. 复现输入就绪证据

```bash
python benchmarks/2026D/run_readiness.py
# CUMCM-2026D: BLOCKED (gate=NOT_RUN)
#   B01_INPUT_READINESS: BLOCKED - Required benchmark attachments are missing.
#     missing: ['attachment_2_result1', 'attachment_2_result2', 'attachment_2_result3', 'attachment_2_result4']
```

该脚本在未 READY 时返回非 0 退出码，这是刻意的。

## 8. 当前状态与边界

- ✅ 题目与附件 1 已入库并固定哈希。
- ❌ 附件 2 缺失，**B01 未通过**，因此本 benchmark **不具备开工条件**。
- ⬜ 即便补齐附件 2，题目识别、建模、计算、验证、论文也**均未执行**。
