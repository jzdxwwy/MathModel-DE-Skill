# 2024E 可执行压力测试方案

2024E“交通流量管控”适合作为 E 类 Skill 的完整回归测试。官方赛题于 2024-09-05 发布，中国大学生在线随后发布了官方赛题讲评。citeturn0search0turn0search3

## Pipeline

```text
raw Excel/CSV
  -> data audit
  -> vehicle-level trajectory reconstruction
  -> time-window EDA
  -> Q1 period segmentation + flow estimation
  -> Q2 signal-control optimization
  -> Q3 cruising-vehicle identification + parking demand
  -> Q4 before/after control evaluation
  -> verification
  -> figures
  -> frozen numbers
  -> paper sections
```

## Q1：时段划分

Baseline：按固定 15/30/60 min 聚合。

Candidate：K-means、层次聚类、变点检测。

Selection：聚类指标 + 时间连续性 + 业务解释性。

输出：各时段边界、方向流量、直行/转向估计及不确定性。

## Q2：信号配时

Baseline：题目给定/现状配时。

Candidate：容量约束下的非线性优化；必要时离散搜索。

Decision variables：周期、各相位绿灯时间及题目允许的其他控制变量。

Hard checks：最小绿灯、周期上下界、相位总时长、题目约束。

评价：平均速度/延误/吞吐量等题目规定指标，并报告优化前后差异。

## Q3：巡游车辆与停车需求

先做规则基线：持续时间、重复经过、低速占比、回访等。

只有存在人工标签时才运行监督分类；无标签时使用聚类/规则，并明确其性质。

停车需求必须由到达、停留时间和容量关系推导，不得直接把巡游车辆数量等同于车位需求。

## Q4：管控效果

优先采用同路段、同时段、管控前后对照；进一步考虑日期和流量基线差异。

可选方法：Bootstrap、置换检验；数据满足条件时再考虑 Difference-in-Differences。

## E题数据门禁

- 时间解析与时区/日期一致
- 车辆 ID/车牌缺失与重复
- 监控点编码统一
- 方向编码统一
- 同车轨迹时间顺序合理
- 异常速度与负时间差
- 假日/平日分布漂移
- 按车辆、日期或时间块避免数据泄漏

## 验证门禁

- 模型输出与原始数据规模一致
- 优化方案满足全部硬约束
- 时段划分对窗口扰动具有稳定性
- 关键结论对参数扰动不敏感，或明确敏感参数
- 所有论文数字均能追溯到 `run_manifest.json`
- 不把参考论文或示例答案中的数字写入程序

## 目标

该文件不是答案模板，而是用于检验 Skill 是否能从真实数据一路生成可复核结果。正式运行必须提供 2024E 原始附件；若附件缺失，不得用猜测数据替代。
