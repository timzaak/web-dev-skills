# Patrol 初始化指引

本页只说明初始化顺序、关键选择和验收点。具体原生工程操作以 [Patrol 官方安装页](https://patrol.leancode.co/documentation) 为准，不在插件内维护第二套逐步教程。

插件当前只把 Android 作为 `t-flutter-demo-*` 自动运行与验收链路的平台；本页的独立 `patrol-test-runner.py` 支持显式选择 iOS，用于目标项目自行运行 Patrol，但不等于 iOS 已进入 Demo 验收门禁。

## 初始化顺序

1. 先读目标项目 `pubspec.yaml`、`pubspec.lock`、Flutter 版本和原生工程，确认 Patrol 是否确实需要。只有权限、通知、WebView、相册或跨 App 等原生 UI 才优先使用 Patrol；其余流程优先普通 `integration_test`。
2. 把 `patrol` 加入 `dev_dependencies`，按[官方兼容表](https://patrol.leancode.co/documentation/compatibility-table)为锁定包版本选择 `patrol_cli`。CI 固定 CLI 版本，运行时不自动升级。
3. 在顶层 `patrol:` 声明真实 `app_name`、Android `applicationId`、iOS Runner bundle id 和可选 flavor。Patrol 4 默认使用 `patrol_test/`，不要与普通 `integration_test/` 混放。
4. 按官方安装页完成实际交付平台的原生接线。Android 重点核对 `PatrolJUnitRunner`、Test Orchestrator 和 App 数据隔离；iOS 重点核对 `RunnerUITests`、依赖方式、scheme/build phase、deployment target 与签名。
5. 忽略 `**/test_bundle.dart`、`.patrol.env` 和 `patrol_test/test-results/`。通过 `rootBundle` 使用的测试 fixture 要加入 `flutter.assets`，凭证不得作为 fixture 提交。

`C:/code/ai/atool` 的实践说明，初始化时最容易遗漏的不是 Dart 测试本身，而是包/CLI 不匹配、原生 runner 没接通、包名或 bundle id 仍是示例值、iOS UI Test 签名不完整。不要跨项目复制 `project.pbxproj`、Team、证书或 bundle id；让 Xcode 写入项目自身配置。

## App 启动约束

Patrol 生成的 `test_bundle.dart` 是测试入口，不会替测试执行生产 `main()`。测试应复用生产 composition root 的可测试初始化函数，再用 `$.pumpWidget()` 或 `$.pumpWidgetAndSettle()` 启动根 Widget。

测试入口不要调用 `WidgetsFlutterBinding.ensureInitialized()`、`runApp()` 或覆盖 `FlutterError.onError`。需要测试环境时只切换配置，不得用 fake repository、Provider override 或单页 Widget 代替真实 Demo 流程。

## 最小验收

```bash
flutter pub get
patrol doctor
dart analyze patrol_test
patrol test --target patrol_test/app_smoke_test.dart --device <device-id>
```

验收标准是至少一个 Dart 用例被发现并通过，不是“App 构建成功”。`Total: 0` 优先核对版本兼容、原生 runner、应用标识和测试目录；Widget 全部找不到时，优先核对是否显式 pump 了 App。

iOS 真机使用 release 构建并完成 App 与 UI Test runner 签名；`patrol develop` 不适合作为 iOS 真机迭代入口。

## 运行脚本

`${CLAUDE_PLUGIN_ROOT}/scripts/patrol-test-runner.py` 迁移并泛化了 `atool` 的 Patrol 批量运行脚本：默认把选中的多个文件交给一次 `patrol test`，利用 test bundling 只构建一次。test bundling 的机制是 `patrol test` 扫描 `patrol_test/` 生成 `test_bundle.dart`，把全部测试编译进单个 app binary，所以只需一次原生构建；每条用例仍各自启动新的 app process，天然隔离并支持 sharding。`--isolate-files` 对每个文件单独 build+test，破坏 bundling，只在需要逐文件继续执行和诊断时使用。

```bash
# Android：一次构建运行全部 Patrol 文件
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/patrol-test-runner.py --device <android-id>

# iOS：显式选择平台和设备
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/patrol-test-runner.py --platform ios --device <ios-id>

# 诊断模式：逐文件运行并汇总
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/patrol-test-runner.py --device <android-id> --isolate-files
```

日常编写与最终验收策略见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/demo-testing.md`。
