# Flutter 用户故事演示（Patrol）

Flutter Demo 是安装到 Android 设备上的用户故事验收层，覆盖真实 App 操作和权限、通知、WebView 等系统 UI；不替代单元、Widget 或普通 integration test。首次接入先看 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/patrol-initialization.md`。

## Structure

```text
patrol_test/
└── <domain>/
    ├── <story>_test.dart
    ├── screens/       # 多个故事复用时才建立
    └── helpers/       # 稳定、无业务断言的复用动作
```

文件顶部记录用户故事来源与 US ID；一个文件只覆盖一个用户故事或强耦合状态流。

## 编写准则

- 只把重要 happy path 和必须经过原生 UI 的路径放进 Flutter Demo；输入校验、边界组合和纯 Flutter 行为下沉到更快的测试层。
- 从生产 composition root 启动，测试显式 pump App。Demo 配置可通过专用 entrypoint 或 `--dart-define` 切换，但不得用 fake 代替真实流程。
- Finder 优先稳定 `ValueKey`，其次 Semantics 和稳定文案；禁止依赖 Widget 位置。断言持久业务结果，不把短暂提示作为唯一结果。
- Flutter 控件使用 Patrol finder；跨平台原生动作优先 `$.platform.mobile`，平台专属行为才使用 Android/iOS API。
- 禁止 `sleep`、真实延迟和无理由的宽松等待。权限弹窗先判断是否可见，以兼容本地 Hot Restart 后的已授权状态。
- 使用隔离测试数据和测试环境；禁止生产凭证、生产写操作和在日志中暴露 secret。

## 快速反馈

Patrol 的主要成本是原生构建、安装和设备启动：

- 编写单文件时使用 `patrol develop --target <file> --device <id>`，首次构建后用 Hot Restart 迭代。注意它不会清除权限、SharedPreferences、文件或原生状态。
- 多文件快速回归使用 `${CLAUDE_PLUGIN_ROOT}/scripts/patrol-test-runner.py`，默认一次构建运行全部选中文件。`--isolate-files` 只用于逐文件诊断。
- 用 Patrol tags 做语义子集回归：在 `patrolTest('...', tags: ['smoke'], ...)` 打标，再经 runner 透传原生过滤参数（用 `--` 分隔，避免与 runner 自身参数歧义）：`uv run ${CLAUDE_PLUGIN_ROOT}/scripts/patrol-test-runner.py -d <id> -- --tags smoke` 或 `-- --exclude-tags='slow'`，支持 `||`、`&&`、`!` 布尔表达式。tags 只用于快速回归，不改变 `t-flutter-demo-run-all` 的全量验收门禁。
- 文件稳定后使用 `/t-tools:t-flutter-demo-run` 产出单故事证据；最终验收才执行 `/t-tools:t-flutter-demo-run-all` 和 `/t-tools:t-flutter-demo-accept`。

## Run

```bash
/t-tools:t-flutter-demo-run patrol_test/auth/password_login_test.dart --device <android-id>
/t-tools:t-flutter-demo-run-all --device <android-id>
/t-tools:t-flutter-demo-accept all --device <android-id>
```

插件首版只支持 Android Demo 验收。证据必须记录设备、OS、Flutter、Patrol package/CLI 版本和实际命令。

官方依据：[Write your first test](https://patrol.leancode.co/documentation/write-your-first-test)、[Patrol test](https://patrol.leancode.co/cli-commands/test)、[Develop](https://patrol.leancode.co/cli-commands)、[Native automation](https://patrol.leancode.co/documentation/native/usage)。

