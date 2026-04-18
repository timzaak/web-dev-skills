# Backend Test Execution Contract

定义 `t-backend-test-run` 的默认执行策略。

## Default Principle

先做最窄、可靠的定向验证；全量测试只作为升级路径，不是默认动作。

## Workflow

1. 分析改动：`git status`, `git diff --name-only`
2. 选择最小可靠测试范围
3. 运行定向测试
4. 解析错误并按根因分组
5. 委派 `backend-dev` 修复生产代码问题
6. 定向复测
7. 只有在定向范围无法可靠覆盖时才升级全量测试

## Scope Mapping

- 单个测试或 helper 影响 => 指向具体测试
- 单 crate / module 影响 => `-E 'package(<crate>)'`
- API 层影响 => `-E 'package(api)'`
- 多处局部影响但仍可收敛 => `package + test(pattern)`
- 跨 crate 或影响不清晰 => 记录原因后升级全量

## Allowed Commands

- `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py`
- `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- <test_name>`
- `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'package(<crate>)'`
- `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'test(<pattern>)'`
- `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'package(<crate>) and test(<pattern>)'`

## Conflict Resolution

当测试与实现冲突时，优先级：

- `docs/user-stories/`
- `docs/prd/`
- 现有稳定测试

若行为仍不明确，升级给用户，不要凭印象修改。
