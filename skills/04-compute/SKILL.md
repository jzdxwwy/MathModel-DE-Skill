# Stage 04 — Compute Skill

## 目的
把 `ModelSpec` 转化为可复现计算，并形成 `RunManifest` 与 `ResultBundle`。

## 核心任务
- 编码
- 参数估计
- 优化 / 预测 / 仿真 / 分类等求解
- 记录环境、参数、随机种子和输入
- 保存原始结果与关键数字

## 输出
- `RunManifest`
- `ResultBundle`

## 工具
Python 模板属于工具层，只按 `ModelSpec` 需要调用。

## Gate
程序“运行成功”不等于模型“计算正确”。结果必须进入 Verification Stage。
