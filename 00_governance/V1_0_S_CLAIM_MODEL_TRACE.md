# V1.0-S：公式/参数级溯源

## 目标
S 将 R 的数值溯源扩展到数学模型结构：
Claim → ModelSpec → equation / parameter

## 确定性规则
- 公式只允许通过结构化 equation_observations 提供；
- 参数只允许通过 parameter_observations 提供；
- equation 采用保守的空白归一化后 SHA256 比较；
- 不做“看起来等价”的代数推理；
- parameter 按 symbol 唯一定位；
- 数值按 atol/rtol 比较；
- 单位若双方均存在必须精确一致；
- model_id 必须一致。

## 安全边界
S 不从自然语言论文正文猜公式/参数，不重算模型，不修改 ModelSpec，不自动选择公式。

## 与 R 的关系
R：Claim → ResultBundle 数值一致性；
S：Claim → ModelSpec 公式/参数一致性。

## 当前限制
- 首版只支持单个 ModelSpec；
- 不做符号代数等价证明；
- 不支持隐式多模型 Claim；
- model-spec.json 路径需要由运行时/建模阶段标准化。

## 测试
已加入单元测试，但尚未实际运行 pytest。
