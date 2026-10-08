# 测试状态（实测证据）

> 本文记录**实际执行过**的测试结果，用于替换此前文档中"尚未运行 pytest"的临时声明。
> 历史版本治理文档（`00_governance/`）是当时会话的记录，保持原样不改写。

## 1. 结论

| 项目 | 结果 |
| --- | --- |
| 命令 | `python -m pytest -q`（仓库根目录） |
| 结果 | **141 passed, 0 failed, 0 errors** |
| 耗时 | 约 4 秒 |
| 基线（修复前） | 3 failed, 138 passed |
| 执行日期 | 2026-10-08 |
| 仓库版本 | `main` @ `9a005f1` |
| 解释器 | CPython 3.14.6 (Windows x64) |
| GitHub Actions | run #52（commit `8eb68a6`）**success**，且 `set -o pipefail` 已生效 |

裸 `pytest`（不带 `-m`）同样可收集全部 141 个用例——这依赖本仓库新增的 `pytest.ini`。

## 2. 修复前基线（3 个真实缺陷）

```
FAILED tests/artifact/test_artifact_contracts.py::test_core_contracts_reject_empty_objects
FAILED tests/runtime/test_v09_b_template_adapter.py::test_regression_template_executes_with_explicit_binding
FAILED tests/verification/test_v10_final_submission_gate.py::test_v10_passes_complete_evidence
3 failed, 138 passed in 5.35s
```

### 2.1 `artifacts/schemas/model-plan.schema.json` 是坏 JSON

文件缺少一个闭合花括号，导致 `selection_principles` 与 `d_or_e_prior` 被错误地嵌套进 `task_models`
的 schema 内部，且根对象没有闭合。52 个 schema 中唯一一个无法解析。

后果不止是测试失败：`tools/modeling/model_plan_builder.py` 实际产出的 ModelPlan 无法通过该契约校验，
所有依赖此 schema 的校验路径都失效。

修复：在 `task_models` 结束后补上闭合花括号，使两个字段回到根 `properties` 层级。

### 2.2 `tools/runtime/template_adapter.py` 在 CSV 输入下崩溃

模板以运行目录作为 CWD 执行，但该目录只在 `_prepare_csv()` 处理非 CSV 输入时才被创建。
CSV 输入路径下 `os.chdir(run_dir)` 抛出 `FileNotFoundError`。

修复：进入 `chdir` 之前显式 `run_dir.mkdir(parents=True, exist_ok=True)`。

### 2.3 Final Submission Gate 测试与实现契约自相矛盾

`test_v10_passes_complete_evidence` 断言 `gate_decision == "PASS"`，但同一次调用把 16 个门禁
显式关闭。按 `00_governance/V1_0_FINAL_SUBMISSION_GATE.md` 第 5 节：

- 任一 `FAIL` → `FAIL`
- 无 `FAIL` 但存在 `NOT_RUN` → `NOT_RUN`
- 全部 `PASS` → `PASS`

被显式关闭的门禁产生 `NOT_RUN`，因此总体**必须**是 `NOT_RUN`。同一仓库的
`tests/integration/test_v10_v2_final_gate_fixture.py` 正是这样断言的（核心证据 PASS，总体 NOT_RUN）。

这是**测试写错了，不是门禁写错了**，所以修的是测试：改为断言必需检查全部 PASS、无阻断失败，
且总体保持 `NOT_RUN`，并补上引用治理契约的说明。门禁语义未改动。

## 3. 同时修复的工程 / CI 缺口

这些不会让本地 pytest 失败，但会让仓库或 CI 在实际使用时失效。

### 3.1 CI 的测试结果不可信（缺少 pipefail）——最严重的一项

三个测试步骤原本都写成：

```bash
python -m pytest ... | tee artifacts/ci/xxx.log
```

GitHub Actions 在 Linux 上的默认 shell 是 `bash -e`，**不包含 `pipefail`**。因此管道的退出码
等于最后一个命令 `tee` 的退出码，恒为 0：pytest 失败不会让步骤失败，`continue-on-error`
永远不会触发，最后那一步 `Fail workflow if any test layer failed` 也就永远不会失败。

**结论：这个工作流此前的绿灯不能作为"测试通过"的证据。**

需要说清楚的边界：GitHub 的步骤耗时是**秒级精度**，而本地 `tests/verification/` 实测只需
0.87 秒。因此 run #50 / #51 记录的 1 秒 / 0 秒 / 2 秒，**既符合"测试真的跑了并通过"，也符合
"测试在导入阶段报错后快速退出"**，单凭耗时无法区分二者。能够确定的是：失败会被管道吞掉。

修复：三个步骤都加 `set -o pipefail`（并补上原先只有第一步才有的 `mkdir -p artifacts/ci`），
保留 `tee` 以继续产出 CI 日志与 JUnit XML。

### 3.2 CI 依赖清单不完整

工作流原先只安装 `pytest jsonschema`，而测试在**导入阶段**就需要 `numpy`、`pandas`、
`scipy`、`sympy`、`scikit-learn`：例如 `tools/runtime/template_adapter.py` 顶层
`import pandas`，`tools/runtime/expression_adapter.py` 顶层 `import numpy / scipy / sympy`，
`tests/smoke_test.py` 顶层 `import numpy / pandas`。缺依赖会让收集阶段直接报错，
而这些错误此前被 3.1 的管道吞掉，表现为"步骤成功"。

修复：新增根目录 `requirements.txt` 作为运行时 + 测试依赖的单一来源，CI 改为
`python -m pip install -r requirements.txt`。

这里需要区分两件事：**测试代码确实在导入阶段依赖这些包**，这由源码直接确定；
而"CI 上是否真的因此失败过"**无法追溯**——修复前的运行无论成败都记为 success，
其日志证据也不足以区分。补全依赖清单本身是正确做法，不依赖上述判定。

### 3.3 裸 `pytest` 无法收集测试

测试以 `tools.*` 导入仓库包，但仓库根不在 `sys.path`。此前只有 `python -m pytest`
能工作，裸 `pytest` 会产生 **46 个收集错误**。

修复：新增 `pytest.ini`（`pythonpath = .`、`testpaths = tests`）。

### 3.4 仓库没有 `.gitignore`

`__pycache__/`、`.pytest_cache/`、`tests/_smoke_workspace/`（由 `tests/smoke_test.py` 生成的
临时产物）会持续污染 `git status`。已补 `.gitignore`；修复后 `git status` 只剩预期的源码改动。

## 4. 复现方式

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

预期输出末行：`141 passed`。

## 5. 本证据的边界（不得夸大）

- 以上本机结果**已由 GitHub Actions 复核**：commit `8eb68a6`（run #52）在 `set -o pipefail`
  生效后仍为 `success`，步骤级 integration / verification / full-regression 均为 `success`，
  最终门禁步骤通过。因为 pipefail 已生效，这次绿灯**能够**在测试失败时变红，与修复前
  "无论成败都绿"不同，因此它才是可信信号。
- 修复前的 CI 绿灯（run #50、#51）无法追溯其真实含义，**不作为"曾经通过"的证据**。
- 测试覆盖的是门禁、契约和证据链的**代码行为**，不代表任何真实 D/E 题已被求解。
- 需要真实运行环境证据的门禁（F7–F15：rebuild、environment closure、clean-room execution、
  execution replay、host/dependency materialization、venv tool execution）在 fixture 中仍然是
  `NOT_RUN`，这是刻意的 fail-closed 设计，**不得**被当作通过。
- `tests/smoke_test.py` 与 `tests/trajectory_smoke_test.py` 被 pytest 当作模块导入（因此
  集合阶段就需要 numpy/pandas），但它们是脚本式冒烟脚本，通过 `__main__` 运行，**贡献 0 个用例**。
- `benchmarks/2024D`、`2024E`、`2025D`、`2025E` 目前只有计划/说明文档，没有真实附件，
  Benchmark 尚未真正执行。
