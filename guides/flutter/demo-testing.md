# Flutter 用户故事演示（Patrol）

Flutter Demo 是安装到 Android 设备上的用户故事验收层。它模拟用户启动 App、输入、导航、确认结果以及操作权限、通知、WebView 等系统 UI；不替代单元、Widget 或普通 integration test。

## Structure

```text
patrol_test/
└── <domain>/
    ├── <story>_test.dart
    ├── screens/       # 仅在多个故事复用时建立
    └── helpers/       # 环境无关的稳定交互 helper
```

文件顶部记录用户故事来源与 US ID。一个文件只覆盖一个用户故事或一个强耦合状态流，场景标题与 Gherkin 验收标准对应。

## App And Data Boundary

- 从生产 composition root 启动；需要测试配置时使用专用 Demo entrypoint 或 `--dart-define`，不得换成 fake repository/Provider。
- 有后端的项目使用专用测试环境、本地容器或 sandbox；无后端项目直接运行。
- 可选环境脚本固定为成对的 `scripts/flutter-demo-start.py` 和 `scripts/flutter-demo-stop.py`。数据准备和清理由目标项目负责。
- 禁止生产凭证、生产写操作和把 secret 写入测试文件或日志。

## Authoring Gate

- Finder：稳定 `ValueKey` > Semantics > 稳定文案；禁止依赖 widget 树位置。
- 断言持久业务结果、页面状态或稳定错误区域，不以自动消失提示作为唯一结果。
- 禁止 `sleep`、真实 `Future.delayed` 和无理由的宽松等待。
- 原生 UI 使用 `$.platform.mobile`；普通 Flutter 控件使用 Patrol finder。
- `patrol_test/test-results/` 必须加入目标项目忽略规则。

## Run

```bash
/t-tools:t-flutter-demo-run patrol_test/auth/password_login_test.dart --device <android-id>
/t-tools:t-flutter-demo-run-all
/t-tools:t-flutter-demo-accept all --device <android-id>
```

首版只把 Android 作为支持和验收平台。设备、OS、Flutter、Patrol package/CLI 版本和实际命令必须写入证据。

