# V0.9-F：Domain Verification Rules

## 1. 目标

V0.9-F 在通用 Verification Gate 之上增加模型族级验证规则：

`ResultBundle + ModelID + Binding → Domain Rules → VerificationReport`

原则仍然是证据优先、缺证据不通过、验证不修改结果。

## 2. 规则覆盖

| 模型族 | 自动检查 | 缺失证据 |
|---|---|---|
| 回归 | R²、MAE、RMSE、可复现性证据 | NOT_RUN |
| 分类 | Accuracy、F1 | NOT_RUN |
| 时间序列 | 时序误差指标、预测步长绑定 | NOT_RUN |
| 优化 | 约束可行性证据 | NOT_RUN |
| 最短路径 | path、distance 输出 | NOT_RUN |
| 蒙特卡洛/敏感性 | 重复次数/置信区间等证据 | NOT_RUN |
| 机理/轨迹 | 输出存在性、稳定性附加验证 | NOT_RUN |

## 3. 规则边界

规则只读取 ResultBundle、ToolDispatch binding 和运行证据，不访问外部网络，不生成新数据，不修改模型结果。

当前规则属于第一版门禁，不等价于完整数学正确性证明。后续可继续加入：单位量纲、残差诊断、交叉验证泄漏检查、约束逐项核验、KKT/边界证据、随机种子与重复次数一致性、图表数据一致性。

## 4. Gate

Domain Rules 与 V0.9-E 通用规则合并：

- 任一 FAIL → `FAIL`
- 无 FAIL 且存在 NOT_RUN/WARN → `PASS_WITH_WARNINGS`
- 全部 PASS → `PASS`

因此领域规则不会把缺失证据提升为 PASS。
