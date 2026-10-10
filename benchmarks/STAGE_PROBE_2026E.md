# 2026E 分阶段能力体检（端到端）

> 本文记录把 **已就绪的真实基准 `CUMCM-2026E`** 沿确定性链路逐阶段跑一遍的结果。
> 目的是定位短板，不是宣称能力。所有结论都来自实际执行，未执行的部分明确标注为未执行。

## 1. 方法与可复现性

探针脚本位于工作区 `D:\0ai\_probe\stage_probe_2026E.py` 与 `followup_probe.py`，
可对任意仓库副本运行：

```bash
python D:\0ai\_probe\stage_probe_2026E.py    # 分阶段结果
python D:\0ai\_probe\followup_probe.py       # 隔离混淆项
```

输入是 `benchmarks/2026E/inputs/` 下已入库并固定 SHA256 的真实附件。

**重要前提**：阶段 00（ProblemSpec）与 01（ProblemMap）在 `tools/runtime/real_host.py` 里依赖 LLM。
本次没有可用 LLM，因此这两个阶段的**任务拆解由人工依据题目原文手写**，并在探针输出中明确标注
"NOT machine-derived"。**本文不对 LLM 的读题/拆题质量作任何论断**；被体检的是 LLM 之后的确定性链路。

## 2. 分阶段结果

| 阶段 | 结果 | 证据 |
| --- | --- | --- |
| 00 Start（题目 → ProblemSpec） | **未执行** | 依赖 LLM，本次无凭据 |
| 01 Analysis（→ ProblemMap） | **未执行** | 同上；探针改用手写 ProblemMap |
| 02 Data（→ DataProfile） | ✅ 通过 | 题目 2037 字符；附件读出 3 个 sheet（2627×10 / 365×2 / 2227×9），真实列名 |
| 03 Modeling（→ ModelPlan） | ⚠️ 部分可用 | 修复前对真实附件**永远判为"无数据"**；修复后能选出数据类模型，但仍有映射缺陷（见 4.4、4.5） |
| 04 Compute（→ ResultBundle） | ❌ 基本不可用 | 12 个模型族只有 **4 个**有可用 adapter；Excel 只能读第一张表 |
| 05 Visualization | **未执行** | 上游未产出结果 |
| 06 Verification | **未执行** | 无 ResultBundle 可验 |
| 07 Writing | **未执行** | 无冻结证据 |
| 08 Final Submission | **未执行** | 同上 |

**结论：真实链路的可用边界止于阶段 04 之前。** 阶段 02 可用，阶段 03 部分可用，阶段 04 起不可用。
因此本 benchmark **没有任何求解结果**，`gate_decision` 仍为 `NOT_RUN`。

## 3. 本轮已修复的缺陷

### 3.1 `_has_tabular_data()` 的前导点不匹配（影响最大）

`build_data_profile()` 把 asset 的 `format` 写成**带点的扩展名**（`".xlsx"`），
而 `tools/modeling/model_selector.py::_has_tabular_data()` 拿它去比对
`{"csv","tsv","xlsx","xls","json"}`（**不带点**），于是恒为 `False`。

同一个仓库的 `tools/modeling/data_binding.py:32` 已经写了 `.lstrip(".")` 做归一化，
所以这是纯疏漏，不是约定分歧。

后果（实测）：一个刚刚被成功解析成 3 张表的 `.xlsx`，在选择层被当成"没有数据"，导致

- `_candidates()` 跳过全部数据类模型族（回归/分类/聚类/PCA）；
- 候选不足 2 个时走 fallback `_candidates("simulation", ...)`；
- 结果是**任何真实附件都只会选出机理仿真/蒙特卡洛**。

修复前 → 修复后（同一份手写 ProblemMap）：

| 子问题 | 修复前选中 | 修复后选中 |
| --- | --- | --- |
| E1（效益随时间变化规律） | `mechanism_simulation`（机理仿真） | `time_series_baseline` ✓ |
| E2（关键词五分类） | `mechanism_simulation`（机理仿真） | `logistic_classification` ✓ |

**为什么此前没被发现**：`tests/modeling/test_model_selector.py` 的 fixture 写的是
`{"format":"csv"}`（无点），与生产代码实际产出的格式不一致，所以测试永远看不到这个分支。
新增回归测试 `test_selector_treats_dotted_extension_as_tabular_data` 锁死该约定。

### 3.2 多分类 `roc_auc` 让分类模板直接崩溃

`05_python/templates/classification_cv.py` 固定使用 `scoring={"roc_auc": "roc_auc"}`。
sklearn ≥ 1.7 对多分类 `roc_auc` 强制要求显式 `multi_class`，否则抛
`ValueError: multi_class must be in ('ovo', 'ovr')`。

实测：任何类别数 > 2 的目标都会让分类模板崩溃——**包括 D/E 题常见的五分类**。
而 2026E 问题 2 恰好要求把关键词分成 5 类。

修复：二分类沿用 `"roc_auc"`，多分类改用
`make_scorer(roc_auc_score, response_method="predict_proba", multi_class="ovr", average="macro")`。
可执行模型族因此从 **2/12 提升到 4/12**。

## 4. 未修复的短板（需要决策，按影响排序）

### 4.1 12 个模型族里 8 个没有 adapter（最致命）

`tools/runtime/template_adapter.py` 的 `template_map` 只映射 4 个 model_id：

| 可用 | 不可用（`no V0.9-B tabular adapter`） |
| --- | --- |
| `linear_regression`、`tree_ensemble_regression`、`logistic_classification`、`tree_ensemble_classification` | `time_series_baseline`、`clustering`、`pca`、`optimization`、`shortest_path`、`monte_carlo`、`sensitivity`、`mechanism_simulation` |

而 2026E 的四个子问题主要落在不可用的那一侧：问题 3 是 0-1 整数规划（`optimization`），
问题 4 是时序预测 + 机会约束（`time_series_baseline` / `monte_carlo`），
问题 1 是综合评价（目录里根本没有对应族）。**模型目录宣称的能力与实际能执行的能力严重不匹配。**

### 4.2 Excel 只能读第一张表

`template_adapter._prepare_csv()` 用 `pd.read_excel(data_path, sheet_name=0)`。
实测：`linear_regression` 绑定真实 `附件1.xlsx` 的 `新注册数`（在 Sheet2）→
`BLOCKED: columns not found: ['新注册数']`。

E 题最关键的数据（每日注册数在 Sheet2、关键词统计在 Sheet3）**在计算层完全不可达**。
阶段 02 已经把每张表解析成独立 asset，但阶段 04 又退回到"一个文件 = 一张表"。

### 4.3 KEYWORDS 里没有 `evaluation`

`classify_text()` 的十个关键词组里**没有"评价"**，因此综合评价类任务
（AHP / 熵权法 / TOPSIS / 灰色关联）既无法被识别，`model_catalog.py` 里也没有对应模型族。
而 E 题问题 1 正是综合评价。目前该子问题只能被误判成 `time_series`。

### 4.4 约束优化被网络优化压过

对任务"在预算约束下选择关键词，最大化综合效益"，候选排序是
`shortest_path=97 > optimization=94`，因为 `shortest_path` 的先验权重和更高，而排序**完全不看
任务是否具有网络结构**。结果把一个预算分配问题判成了最短路问题。

### 4.5 时序模板缺少特征工程，且 `TIME_COL` 注不进去

- `time_series_cv.py` 的 `FEATURES` 默认为空；实测 `FEATURES=[]` 时直接
  `ValueError: at least one array or dtype is required`——**它不会自己构造滞后/季节特征**。
  探针手工加了一列一日滞后后才跑通（354 折）。
- 该模板声明了 `TIME_COL="time"`，但 `template_adapter` 只注入
  `DATA_PATH/TARGET/FEATURES/SEED/TEST_SIZE/N_SPLITS`，**不注入 `TIME_COL`**，
  所以遇到中文时间列（如 `日期`）会在 `sort_values` 处失败。
- 注：验证时发现 `mean_MAE == mean_RMSE`（354 折全部相等）。这**不是**缺陷：
  `TEST_HORIZON=1` 使每折只有 1 个测试点，单点上 MAE 与 RMSE 必然相等。

### 4.6 真实附件的表头带尾随空格

`附件1.xlsx` 的 Sheet2 真实表头是 `'新注册数 '`（**尾随一个空格**）。
而 `_xlsx_profile()` 会 `strip()` 后写进 DataProfile（`新注册数`）。
两者不一致：按 DataProfile 里的列名直接去绑定 pandas 列会 `KeyError`。
清洗与绑定之间缺少一个显式的"列名规范化"契约。

### 4.7 阶段 00/01 无法脱离 LLM

`real_host.py` 用自然语言指令要求模型返回 JSON ProblemSpec / ProblemMap。
在没有 LLM 凭据的环境里，确定性链路**无法自主完成读题与拆题**，
也就无法从"附件"一路走到"结果"，除非人工补上这两步。

## 5. 后续修复进展（第 3 轮）

上表 7 项短板中，已关闭 3 项：

| 短板 | 状态 | 修复方式 |
| --- | --- | --- |
| 4.1 8 个模型族无 adapter | **部分关闭，且重新定性** | 见下节：其中 3 个是**玩具模板**，接线会伪造结果 |
| 4.2 Excel 只能读第一张表 | ✅ 已修复 | 绑定新增 `sheet`（表名或 0 基索引），并按 DataProfile 的约定 strip 表头 |
| 4.5 时序模板无特征工程 / `TIME_COL` 注不进去 | ✅ 已修复 | adapter 注入 `TIME_COL`/`TEST_HORIZON`/`MIN_TRAIN`；无特征列时确定性构造 `lag1_target` 并写入 manifest |
| 4.6 表头尾随空格 | ✅ 已修复 | `_prepare_csv` 统一 strip 列名 |

### 5.1 4.1 需要重新定性：这不是"缺 adapter"，而是"接上就会伪造结果"

逐一核对 `05_python/templates/` 的输入契约后发现，12 个模型族的真实情况是：

| 类别 | 模型族 | 说明 |
| --- | --- | --- |
| 可执行 | `linear_regression`、`tree_ensemble_regression`、`logistic_classification`、`tree_ensemble_classification`、`time_series_baseline` | 数据驱动，走模块属性注入 |
| 数据驱动但契约不同 | `shortest_path`、`mechanism_simulation` | 前者 `TARGET` 是**终点节点**而非目标列；后者走 **CLI 参数**而非模块属性 |
| **玩具示例，接上即伪造** | `optimization`、`monte_carlo`、`sensitivity` | 目标函数/事件**硬编码**，完全**不读外部数据** |
| 根本没有实现 | `clustering`、`pca` | 目录把它们指向 `model_compare.py`，而那是回归对比，不是聚类/PCA |

三个玩具模板的证据（源码注释即为作者所写）：

- `optimization.py`：`objective()` = `(x0-3)² + 2(x1-5)²`，注释 "Toy objective: replace with the contest objective."，
  manifest 里 `input_hash: "NO_EXTERNAL_INPUT"`；
- `monte_carlo.py`：`simulation()` = `(normal > 1.645)`，注释 "Replace this toy event..."；
- `sensitivity.py`：`objective()` = `2x1 + 0.5x2² - x3`，注释 "Toy objective; replace this with the real contest model"。

若把它们当作 2026E 的 solver 接上，问题 3 会得到一个玩具二次函数的 SLSQP 解、
问题 4 会得到 P(N(0,1) > 1.645) ≈ 5%，**并且带着真实 input hash、RUN_COMPLETE 状态和
可追溯的证据链**——这正是本项目要防的"看起来完整但结果是编的"。

因此第 3 轮没有给它们补 adapter，而是加了**显式拒绝**：`template_adapter` 现在按模板能力分类，
对玩具模板、argv 契约模板、network 契约模板、无实现族分别给出不同的、可执行的拒绝理由。

### 5.2 阶段 04 现在能在真实附件上算出东西

`execute_tabular_template` 在真实 `附件1.xlsx` 上实测：

```
time_series_baseline  sheet="Sheet2"  time_col="日期"  target="新注册数"
  -> EXECUTED
     input_hash       : 3bba8e4e117ef55a8dcf52ec...
     features         : ['lag1_target']    (derived: target(t-1))
     rolling folds    : 354
     mean MAE / RMSE  : 68.9759 / 68.9759
  -> canonical ResultBundle: status=VALIDATED, schema valid=True
```

这是本项目**第一次用真实竞赛数据跑出可追溯的规范结果**（注意：这只是问题 4 的一个
时序基线，**不是**对 2026E 的完整解答）。

仍待解决：`clustering`/`pca`/`mechanism_simulation`/`shortest_path` 无可用实现或契约不符；
阶段 00/01 仍无法脱离 LLM。

## 6. 边界（不得夸大）

- 本轮只体检了**确定性链路**，且 ProblemMap 是人工手写的；**未**评估 LLM 的读题/拆题质量。
- 没有产出任何一道题的答案；没有生成图表、验证报告或论文。
- 阶段 05–08 **完全未执行**，因此关于可视化、验证、写作、交付的能力**没有任何证据**，
  既不能说它们可用，也不能说它们不可用。
- 第 5.2 节的结果是问题 4 的**时序基线**，只覆盖 `新注册数` 一列；
  2026E 的其余子问题（策略诊断、关键词五分类、逐日投放优化）**仍未求解**。
- 参考解（另一套 Skill 的赛期产出）在本次体检中**未被使用**，仅存在于工作区作为对照。
