# `tests_to_run` Contract

## Required Fields

每个 `tests_to_run` 条目必须包含：

- `layer`: `backend | frontend | miniapp | demo`
- `command`: 可直接执行的命令
- `reason`: 为什么这条补测与本次修改直接相关
- `required`: 是否必须通过；默认 `true`

## Allowed Commands

- `backend`: `uv run scripts/backend-test.py -- [filter]`（无 filter 时也写为 `uv run scripts/backend-test.py --`）
- `backend`: Java/Spring 质量检查命令，仅在修改影响编译、静态检查或格式检查时返回：
  - Maven：`cd backend && mvn test`、`cd backend && mvn verify`，或目标项目 `pom.xml` 已配置的质量检查 goal
- `frontend`: `cd frontend && npm run test:run -- [pattern]`
- `miniapp`: `cd miniapp && npm run typecheck` 或 `cd miniapp && npm run build:weapp`
- `demo`: `uv run scripts/demo-test-runner.py "[测试文件]" --run-id [RUN_ID] --grep "[测试标题]"`

## Rules

- 至少返回 1 条与当前修改直接相关的补测。
- 触达多层改动时，按 `backend -> frontend -> miniapp -> demo` 顺序提供建议；未启用 miniapp 的项目跳过 miniapp 层。
- 不要返回全量测试，除非无法可靠收敛影响范围，并在 `reason` 中说明原因。
- 后端静态质量检查必须使用 Java/Spring 项目的 Maven 命令；不得返回非 Java 后端工具链命令。
- 若修复 agent 无法给出可靠补测，必须显式说明原因，而不是返回空数组。
