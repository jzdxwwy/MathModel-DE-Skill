# Stage 04 — Compute Skill

## V0.9-C 目标
把已通过 Model Gate 的 `ModelSpec + data_binding` 转化为真实、可复现、可审计的数值计算。

## 执行链
`ModelSpec → explicit binding → ToolDispatchPlan → ToolRegistry → numerical adapter → RunManifest/ResultBundle`

## V0.9-C 已接通
- E 型表格：线性回归、树模型比较、逻辑回归分类
- 时间序列：rolling-origin Ridge 验证
- 网络：Dijkstra 最短路径
- 轨迹/事件流：有序事件与观测转移重构
- 优化：显式目标函数 + 变量 + 边界 + 不等式约束 → SLSQP
- 敏感性：显式目标函数 + 基准参数 + 网格 → OAT
- Monte Carlo：显式事件表达式 + 随机变量分布 + N + seed

## 安全与真实性
1. LLM 只能提出 `data_binding`，不能提交 Python 代码。
2. 缺少数据路径、目标列、变量、公式、分布或约束等必要信息时返回 `INPUT_BLOCKED`。
3. 表达式执行只接受声明变量和白名单数学函数；禁止 import、lambda、语句和任意代码。
4. 不得把模板演示目标、默认参数或猜测值冒充竞赛题真实模型。
5. Tool Registry 是封闭集合，禁止动态执行任意工具名。

## ResultBundle
计算结果必须映射到正式 `ResultBundle`：`outputs / metrics / artifacts / provenance`。程序退出码成功不等于数学正确；Verification Stage 仍必须检查公式、单位、可行性、误差和稳健性。

## Gate
- Binding Gate：输入契约完整
- Execution Gate：工具实际运行完成
- ResultBundle Gate：Schema 合法
- Verification Gate：数学正确性另行判定
