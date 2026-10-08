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

## 3. 同时修复的工程/CI 缺口

这些不会让本地 pytest 失败，但会让仓库或 CI 在实际使用时失效。

### 3.1 CI 依赖清单不完整

`.github/workflows/v10-v3-integration.yml` 原先只安装 `pytest jsonschema`，而
`tests/` 与 `tools/` 在导入阶段就需要 `numpy`、`pandas`、`scipy`、`sympy`、`scikit-learn`。
其他步骤先不论，仅 full-regression 就必然失败。

修复：新增根目录 `requirements.txt` 作为运行时 + 测试依赖的单一来源，CI 改为
`python -m pip install -r requirements.txt`。

### 3.2 裸 `pytest` 无法收集测试

测试以 `tools.*` 导入仓库包，但仓库根不在 `sys.path`。此前只有 `python -m pytest`
能工作，裸 `pytest` 会产生 **46 个收集错误**。

修复：新增 `pytest.ini`（`pythonpath = .`、`testpaths = tests`）。

### 3.3 仓库没有 `.gitignore`

`__pycache__/`、`.pytest_cache/`、`tests/_smoke_workspace/`（由 `tests/smoke_test.py` 生成的
临时产物）会持续污染 `git status`。已补 `.gitignore`；修复后 `git status` 只剩预期的源码改动。

## 4. 复现方式

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

预期输出末行：`141 passed`。

## 5. 本证据的边界（不得夸大）

- 以上是**本机**代码级单元/集成测试结果。**尚未**观察到 GitHub Actions 上的真实 CI 运行；
  工作流改动要推送后才能验证。
- 测试覆盖的是门禁、契约和证据链的**代码行为**，不代表任何真实 D/E 题已被求解。
- 需要真实运行环境证据的门禁（F7–F15：rebuild、environment closure、clean-room execution、
  execution replay、host/dependency materialization、venv tool execution）在 fixture 中仍然是
  `NOT_RUN`，这是刻意的 fail-closed 设计，**不得**被当作通过。
- `tests/smoke_test.py` 与 `tests/trajectory_smoke_test.py` 被 pytest 当作模块导入（因此
  集合阶段就需要 numpy/pandas），但它们是脚本式冒烟脚本，通过 `__main__` 运行，**贡献 0 个用例**。
- `benchmarks/2024D`、`2024E`、`2025D`、`2025E` 目前只有计划/说明文档，没有真实附件，
  Benchmark 尚未真正执行。
