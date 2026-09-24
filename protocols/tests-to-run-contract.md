# `tests_to_run` Contract

## Required Fields

每个 `tests_to_run` 条目必须包含：

- `layer`: `backend | frontend | extension | miniapp | flutter | web-demo | extension-demo | flutter-demo`
- `command`: 可直接执行的命令
- `reason`: 为什么这条补测与本次修改直接相关
- `required`: 是否必须通过；默认 `true`

## Allowed Commands

- `backend`: `uv run scripts/backend-test.py -- [filter]`（无 filter 时也写为 `uv run scripts/backend-test.py --`）
- `frontend`: `cd frontend && npm run test:run -- [pattern]`
- `extension`: 在实际扩展目录运行项目定向测试（默认 `cd extension && npm run test:run -- [pattern]`）；类型/配置变更可给项目等价类型检查（`compile` 或 `type-check`）和 `build`，说明与变更的关系。
- `miniapp`: `cd miniapp && npm run typecheck` 或 `cd miniapp && npm run build:weapp`
- `flutter`: `cd <flutter-dir> && flutter test [定向路径]`，按需使用 `flutter analyze`、`flutter test integration_test/... -d <device-id>` 或 `patrol test --target ...`
- `web-demo`: `uv run scripts/web-demo-test-runner.py "[测试文件]" --run-id [RUN_ID] --grep "[测试标题]"`
- `extension-demo`: `uv run scripts/web-demo-test-runner.py "demo/e2e/extension/[测试文件]" --run-id [RUN_ID] [--no-auto-env] --grep "[测试标题]"`
- `flutter-demo`: `uv run scripts/flutter-demo-test-runner.py "[测试文件]" --run-id [RUN_ID] --device [ANDROID_DEVICE_ID]`

扩展独立 Demo 使用 fixture 管理环境时，extension-demo 命令保留 `--no-auto-env`；环境选择按 `${CLAUDE_PLUGIN_ROOT}/guides/extension/demo-testing.md`。

## Rules

- 至少返回 1 条与当前修改直接相关的补测。
- 触达多层改动时，按 `backend -> frontend -> extension -> miniapp -> flutter -> web-demo -> extension-demo -> flutter-demo` 顺序提供建议；未启用的层跳过。
- 不要返回全量测试，除非无法可靠收敛影响范围，并在 `reason` 中说明原因。
- 若修复 agent 无法给出可靠补测，必须显式说明原因，而不是返回空数组。
