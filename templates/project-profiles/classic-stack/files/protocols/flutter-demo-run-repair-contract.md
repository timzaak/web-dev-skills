# Flutter Demo Run Repair Contract

本协议是 `t-flutter-demo-run` 与 `t-flutter-demo-run-all` 共享的 Android Patrol 单文件运行、诊断、修复和回归契约。

## Test And Evidence Shape

- 测试文件位于 `patrol_test/<domain>/<story>_test.dart`，文件顶部引用 `docs/user-stories/...` 及稳定 US ID（交付测试文件不得引用 `.ai/user-stories/...`，见 `${CLAUDE_PLUGIN_ROOT}/protocols/code-comment-contract.md`）。
- 一个文件覆盖一个用户故事或单一强耦合状态流；普通 Flutter 交互与原生 UI 都由 Patrol 驱动。
- 使用生产 composition root 或只改变环境配置的 Demo entrypoint。禁止以 Provider fake、mock repository 或直接构造单页代替用户故事演示。
- 日志写入 `patrol_test/test-results/runs/<run-id>/patrol-output.log`，测试资产 authoring 时确保 `patrol_test/test-results/` 被忽略。

Runner 最后一行必须为：

```text
Result: {"success":"true|false","fixed":"true|false","logs":"patrol_test/test-results/runs/...","exitCode":0,"testFile":"patrol_test/...","runId":"...","duration":1.2,"device":"...","platform":"android","error":""}
```

编排层将 camelCase 映射为 snake_case。非零退出且无合法 Result 行视为失败，保留输出尾部作为错误证据。

## Preconditions

- 读取目标项目 `pubspec.yaml`、`pubspec.lock` 和 `patrol.test_directory`；默认目录为 `patrol_test/`。
- 执行 `patrol doctor`。CLI 必须与项目锁定的 Patrol 4.x 兼容，不在运行时自动升级。
- `--device` 必须是受支持的 Android 设备。未传时只能自动选择唯一 Android 设备；零个或多个候选均停止。
- `scripts/flutter-demo-start.py` 与 `scripts/flutter-demo-stop.py` 是可选环境入口，但必须成对存在。不存在表示 App 无需外部环境，不得强制创建后端。

## Single-file Loop

1. 执行整个 Patrol 文件：`flutter-demo-test-runner.py <file> --device <id>`。
2. 通过则返回 `fixed=false`。
3. 失败则调用 `flutter-demo-diagnose`，以 Patrol 输出、Flutter 日志、测试代码和相关用户故事为证据。
4. 按诊断分发到 `flutter-demo-dev | flutter-dev | backend-dev | manual`，执行符合 `tests-to-run-contract.md` 的最小补测后重跑整文件。
5. 最多六轮。Patrol 首版没有稳定的标题过滤契约，不伪造逐用例 grep；修复闭环以文件为单位。

环境或设备前置条件失败时不得修改业务代码。环境脚本产生的数据清理由项目脚本负责；停止脚本失败必须写入结果，不得静默忽略。

## Batch

批量发现 `patrol_test/**/*_test.dart`，排除 `test-results/`，逐文件串行运行并持久化 checkpoint。支持 fresh 和 `continue`；首版不提供依赖 Playwright 日志格式的 scan/cluster。

