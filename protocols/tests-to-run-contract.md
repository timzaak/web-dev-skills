# `tests_to_run` Contract

## Required Fields

每个 `tests_to_run` 条目必须包含：

- `layer`: `backend | frontend | miniapp | flutter | web-demo | flutter-demo`
- `command`: 可直接执行的命令
- `reason`: 为什么这条补测与本次修改直接相关
- `required`: 是否必须通过；默认 `true`

## Allowed Commands

- `backend`: `uv run scripts/backend-test.py -- [filter]`（无 filter 时也写为 `uv run scripts/backend-test.py --`）
- `frontend`: `cd frontend && npm run test:run -- [pattern]`
- `miniapp`: `cd miniapp && npm run typecheck` 或 `cd miniapp && npm run build:weapp`
- `flutter`: `cd <flutter-dir> && flutter test [定向路径]`，按需使用 `flutter analyze`、`flutter test integration_test/... -d <device-id>` 或 `patrol test --target ...`
- `web-demo`: `uv run scripts/web-demo-test-runner.py "[测试文件]" --run-id [RUN_ID] --grep "[测试标题]"`
- `flutter-demo`: `uv run scripts/flutter-demo-test-runner.py "[测试文件]" --run-id [RUN_ID] --device [ANDROID_DEVICE_ID]`

## Rules

- 至少返回 1 条与当前修改直接相关的补测。
- 触达多层改动时，按 `backend -> frontend -> miniapp -> flutter -> web-demo -> flutter-demo` 顺序提供建议；未启用的层跳过。
- 不要返回全量测试，除非无法可靠收敛影响范围，并在 `reason` 中说明原因。
- 若修复 agent 无法给出可靠补测，必须显式说明原因，而不是返回空数组。
