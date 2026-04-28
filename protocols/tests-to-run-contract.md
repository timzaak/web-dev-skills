# `tests_to_run` Contract

用于 `t-demo-run` 修复门禁的统一契约。所有会返回补测建议的修复 agent 都应遵循这一结构。

## Required Fields

每个 `tests_to_run` 条目必须包含：

- `layer`: `backend | frontend | miniapp | demo`
- `command`: 可直接执行的命令
- `reason`: 为什么这条补测与本次修改直接相关
- `required`: 是否必须通过；默认 `true`

## Allowed Commands

- `backend`: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- [filter]`
- `frontend`: `cd frontend && npm run test:run -- [pattern]`
- `miniapp`: `cd miniapp && npm run typecheck` 或 `cd miniapp && npm run build:weapp`
- `demo`: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py "[测试文件]" --run-id [RUN_ID] --grep "[测试标题]"`

## Rules

- 至少返回 1 条与当前修改直接相关的补测。
- 触达多层改动时，按 `backend -> frontend -> miniapp -> demo` 顺序提供建议；未启用 miniapp 的项目跳过 miniapp 层。
- 不要返回全量测试，除非无法可靠收敛影响范围，并在 `reason` 中说明原因。
- 若修复 agent 无法给出可靠补测，必须显式说明原因，而不是返回空数组。
