# Flutter 用户故事演示与 Patrol 初始化

Flutter Demo 是安装到 Android 设备上的用户故事验收层，覆盖真实 App 操作和权限、通知、WebView 等系统 UI；局部测试仅补 Demo/集成验证难稳定覆盖的重要缺口，不要求逐层重复覆盖。

## 1. 目录结构与编写准则

```text
patrol_test/
└── <domain>/
    ├── <story>_test.dart
    ├── screens/       # 多个故事复用时才建立
    └── helpers/       # 稳定、无业务断言的复用动作
```

- 文件顶部按 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md` 的 Story Traceability 记录稳定 US ID，可附有效正式故事路径；草稿真实路径保留在任务/Handoff，不写入交付代码。一个文件只覆盖一个用户故事或强耦合状态流。
- 优先用 Flutter Demo 覆盖重要用户路径和必须经过原生 UI 的行为；纯 Flutter 边界仅在存在重要缺口时按 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/testing.md` 补少量局部测试。
- 从生产 composition root 启动，测试显式 pump App。Demo 配置可通过专用 entrypoint 或 `--dart-define` 切换，但不得用 fake 代替真实流程。
- Finder 优先稳定 `ValueKey`，其次 Semantics 和稳定文案；禁止依赖 Widget 位置。断言持久业务结果，不把短暂提示作为唯一结果。
- Flutter 控件使用 Patrol finder；跨平台原生动作优先 `$.platform.mobile`，平台专属才用 Android/iOS API；禁止 `sleep`、真实延迟和无理由宽松等待；权限弹窗先判断是否可见以兼容 Hot Restart。
- 使用隔离测试数据和测试环境；禁止生产凭证、生产写操作和在日志中暴露 secret。

## 2. 快速反馈与运行入口

Patrol 的主要成本是原生构建、安装和设备启动：

- 编写单文件时用 `patrol develop --target <file> --device <id>`（Hot Restart 迭代；注意不会清除权限、SharedPreferences、文件或原生状态）。
- 多文件快速回归用 `${CLAUDE_PLUGIN_ROOT}/scripts/patrol-test-runner.py`，默认将选中文件交给一次 `patrol test`（利用 test bundling 编译进单个 app binary，仅一次原生构建，每条用例仍独立 app process 隔离）；`--isolate-files` 仅用于逐文件诊断。
- 用 Patrol tags 做语义子集回归：`patrolTest('...', tags: ['smoke'], ...)` 配合 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/patrol-test-runner.py -d <id> -- --tags smoke` 或 `-- --exclude-tags='slow'`（支持 `||`、`&&`、`!`）。tags 只用于快速回归，不改变 `t-flutter-demo-run-all` 全量验收门禁。
- 正式故事证据与验收入口（插件当前自动运行与验收链路只支持 Android，独立 `patrol-test-runner.py` 可显式选 `--platform ios` 供目标项目自跑）。文件稳定后用 `t-flutter-demo-run` 产出单故事证据；验收选择受影响范围的 `t-flutter-demo-accept`；仅发布门禁、无法可靠收敛影响范围或用户要求时执行 `t-flutter-demo-run-all`，显式 run-all 的全量门禁保持不变：

```bash
/t-tools:t-flutter-demo-run patrol_test/auth/password_login_test.dart --device <android-id>
/t-tools:t-flutter-demo-run-all --device <android-id>
/t-tools:t-flutter-demo-accept all --device <android-id>
```

证据必须记录设备、OS、Flutter、Patrol package/CLI 版本和实际命令。

## 3. Patrol 首次接入与初始化指引

具体原生工程步骤以 [Patrol 官方安装页](https://patrol.leancode.co/documentation) 为准，本节约束初始化顺序与验收点：

1. 先读目标项目 `pubspec.yaml`、`pubspec.lock`、Flutter 版本和原生工程，确认是否需要原生 UI 自动化；无原生 UI 需求时优先普通 `integration_test`。
2. 把 `patrol` 加入 `dev_dependencies`，按 [官方兼容表](https://patrol.leancode.co/documentation/compatibility-table) 为锁定包版本选择 `patrol_cli`；CI 固定 CLI 版本，运行时不自动升级。
3. 在顶层 `patrol:` 声明真实 `app_name`、Android `applicationId`、iOS Runner bundle id 和可选 flavor；Patrol 4 默认使用 `patrol_test/`，不与 `integration_test/` 混放。
4. 完成实际交付平台的原生接线：Android 核对 `PatrolJUnitRunner`、Test Orchestrator 与 App 数据隔离；iOS 核对 `RunnerUITests`、依赖方式、scheme/build phase、deployment target 与签名（勿跨项目复制 `project.pbxproj`、Team、证书或 bundle id）。
5. 忽略 `**/test_bundle.dart`、`.patrol.env` 和 `patrol_test/test-results/`；通过 `rootBundle` 使用的 fixture 加入 `flutter.assets`，凭证不得提交。
6. **App 启动约束**：`test_bundle.dart` 不替测试执行生产 `main()`，测试复用生产 composition root 的可测试初始化函数，再用 `$.pumpWidget()` / `$.pumpWidgetAndSettle()` 启动根 Widget；不调用 `WidgetsFlutterBinding.ensureInitialized()`、`runApp()` 或覆盖 `FlutterError.onError`。

最小初始化验收（标准是至少一个 Dart 用例被发现并通过，而非仅“App 构建成功”；`Total: 0` 先核对版本兼容/原生 runner/标识/目录，Widget 全部找不到时先核对是否显式 pump 了 App；iOS 真机用 release 构建并完成 App 与 UI Test runner 签名，`patrol develop` 不作为 iOS 真机迭代入口）：

```bash
flutter pub get
patrol doctor
dart analyze patrol_test
patrol test --target patrol_test/app_smoke_test.dart --device <device-id>
```

官方依据：[Write your first test](https://patrol.leancode.co/documentation/write-your-first-test)、[Patrol test](https://patrol.leancode.co/cli-commands/test)、[Develop](https://patrol.leancode.co/cli-commands)、[Native automation](https://patrol.leancode.co/documentation/native/usage)。
