# Backend Test Execution Contract

## Scope

- 适用于 backend/test `test_item_type: runner`。
- 不适用于场景测试 authoring；authoring 由 `backend-test` item 完成。
- runner item 的 `agent` 必须为 `general-purpose`，并直接按本协议执行。

## Default Principle

先做最窄、可靠的定向验证；全量测试只作为升级路径，不是默认动作。

runner 不得因为“省事”或“保证覆盖”直接执行全量 `uv run scripts/backend-test.py --`。全量只能在定向命令无法稳定选中预期测试、影响范围无法收敛、或发布/验收门禁明确要求时使用，并必须记录升级原因。

## Workflow

- 分析改动：`git status`, `git diff --name-only`。
- 读取 runner item 的 `Expected Test Manifest`，建立预期测试函数清单。
- 运行 `uv run scripts/check-test-runner-coverage.py <feature> --layer backend`，或等价执行 `cargo nextest list`，确认定向命令会选中全部预期测试。
- 选择最小可靠测试范围。
- 若 item validation 只有全量 `uv run scripts/backend-test.py --` 且没有升级原因，先修正为定向命令或返回任务规划缺陷；不得直接执行全量。
- 运行定向测试，覆盖当前 runner item 汇总的全部相关 authoring item。
- 解析失败并记录命令、测试名、文件/行、失败类型和关键消息。
- 判断所有权：机械性测试问题可修测试；生产代码问题委派 `backend-dev`。
- 定向复测。
- 只有在定向范围无法可靠覆盖时才升级全量测试。

## Scope Mapping

- 单个测试或 helper 影响 => 指向具体测试。
- 多个相关测试 authoring item 影响同一业务场景 => 使用同一 package/module/test pattern 集中覆盖。
- 单 crate / module 影响 => `-E 'package(<crate>)'`。
- API 层影响 => `-E 'package(api)'`。
- 多处局部影响但仍可收敛 => `package + test(pattern)`。
- 跨 crate 或影响不清晰 => 记录原因后升级全量。

## Backend Test Command

后端测试统一使用：

```bash
uv run scripts/backend-test.py -- [filter]
```

常用形态：

```bash
uv run scripts/backend-test.py --
uv run scripts/backend-test.py -- <test_name>
uv run scripts/backend-test.py -- -E 'package(<crate>)'
uv run scripts/backend-test.py -- -E 'test(<pattern>)'
uv run scripts/backend-test.py -- -E 'package(<crate>) and test(<pattern>)'
```

runner 命令以覆盖来源和变更范围推导；同一业务场景或 package/module 使用同一个最小可靠命令。全量 `uv run scripts/backend-test.py --` 仅在定向范围不可靠或门禁要求时使用。

`[filter]` 是可选参数；没有 filter 时命令就是 `uv run scripts/backend-test.py --`。

## Coverage Manifest

backend/test runner item 必须包含 `Expected Test Manifest`：

| 字段 | 说明 |
|---|---|
| source_item | 产生或修改测试的 authoring item |
| test_file | 测试文件路径 |
| test_name | Rust 测试函数名 |
| runner_command | 预期覆盖该测试的定向命令 |

runner 完成报告必须写明 expected/selected/missing 数量。若 `cargo nextest list` 无法选中任一预期测试，runner 不得继续声称测试覆盖完成；应修正 runner 命令或返回覆盖缺口。

## Ownership

优先级：

```text
User Story > PRD > Existing Stable Tests > Current Implementation
```

- 实现违背 User Story/PRD：委派 `backend-dev` 修复生产代码。
- 测试有机械性问题：runner 可修 imports、模块注册、helper 调用签名、明显路径错误。
- 测试语义可能错误：停止并输出诊断报告；不得修改断言、状态码预期、权限预期或业务规则预期。
- User Story/PRD 不清楚：停止并请求澄清。

委派 `backend-dev` 时必须明确：

- 不得修改 `backend/**/tests/scenarios/**`。
- 不得修改任何 `*_scenarios.rs`。
- 不得改变场景测试断言、状态码预期、权限预期或业务规则预期。
- 如果必须改测试语义，返回 `requires_test_semantics_change` 和证据。

## Stop Report

测试语义冲突时输出：

```markdown
# Backend Test Run Blocked: Test Semantics Need Decision

## Failure
- Command: `<command>`
- Test: `<test_name>`
- Assertion: `<expected vs actual>`

## Evidence
- User Story: `<path and section>`
- PRD: `<path and section>`
- Existing tests: `<paths>`

## Diagnosis
The runner cannot safely decide whether to change test semantics or implementation.

## Required Decision
Choose whether to return this to `backend-test` for scenario correction or send it to `backend-dev` for implementation correction.
```
