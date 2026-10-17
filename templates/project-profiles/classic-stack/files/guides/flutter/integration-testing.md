# Flutter 集成测试与 Patrol 原生自动化

定位：`integration_test` 验证跨组件集成；Patrol 也可处理原生平台 UI。按用户故事组织、可运行和可验收的 Android 演示统一见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/demo-testing.md`。它们都不替代单元/widget 测试。

## 载体与命令

- Android、iOS、desktop：官方 `integration_test`。
- Web：仍可使用 `integration_test`，但官方流程需要 ChromeDriver、driver 文件和 `flutter drive`。
- 权限弹窗、通知、WebView、应用切换等原生 UI：目标项目已采用 Patrol 时使用 Patrol；否则在设计中指定等价方案。
- 用户故事演示：使用 `flutter-demo` phase 和 `patrol_test/`，不混入普通 `flutter/test` runner。

```bash
flutter devices

# Android / iOS / desktop
flutter test integration_test/login_flow_test.dart -d <device-id>

# Web：先启动匹配版本的 ChromeDriver
flutter drive \
  --driver=test_driver/integration_test.dart \
  --target=integration_test/login_flow_test.dart \
  -d chrome
```

CI 记录设备、OS、Flutter 版本和实际命令。只有真实硬件能力或模拟器无法复现的流程才强制真机。

## Finder 规则

优先级：稳定 Key > Semantics label > 稳定文案 > icon/type。禁止依赖 widget 树位置或深层 `find.descendant`。

关键交互控件使用 `ValueKey`：

```text
<domain>-<entity>-<action|field>
```

例如 `login-email-input`、`login-submit-button`。动态列表项可使用稳定业务 ID；装饰性控件不加测试 Key。

测试与 Widget 共用的 Key 字符串集中在单一文件（如 `integration_test_keys.dart`），按页面分组后再包成一个总实例，禁止在测试和 Widget 里散落重复字符串：

```dart
class SignInPageKeys {
  final emailTextField = const Key('login-email-input');
  final signInButton = const Key('login-submit-button');
}

class Keys {
  final signInPage = SignInPageKeys();
}

final keys = Keys();
```

主链路存在多个用例复用时，将 finder/动作提取到 `integration_test/screens/`；断言留在测试文件。不要为单个短用例强制创建 Screen Object。

## Patrol 4

首次接入或排查原生 runner 时，遵循 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/patrol-initialization.md`。先读目标项目 `pubspec.lock` 并按官方兼容表选择 `patrol_cli`，不要只看 `pubspec.yaml` 的版本约束，也不要在运行时自动升级。

已完成初始化的项目按 Patrol 4.x API 编写：

```dart
import 'package:patrol/patrol.dart';

void main() {
  patrolTest('grants location and shows map', ($) async {
    await $.pumpWidgetAndSettle(const MyApp());
    await $('开启定位').tap();
    await $.platform.mobile.grantPermissionWhenInUse();
    expect($(const ValueKey('map-root')), findsOneWidget);
  });
}
```

```bash
patrol doctor
patrol test --target patrol_test/location_test.dart --device <device-id>
```

Patrol UI 测试不能用普通 `flutter test`。跨 Android/iOS 的原生移动端动作优先使用 `$.platform.mobile`；只有平台专属行为才使用 `$.platform.android` 或 `$.platform.ios`。Web 使用 `$.platform.web`。

## 门禁

- 改动影响重要用户用例时，运行对应 integration test。
- 原生 UI 流程提供 Patrol 或设计批准的等价自动化证据。
- 不使用 `sleep`/真实延迟，不放宽断言绕过失败。
- 保留有独立诊断价值的快速测试，避免逐断言机械复制 E2E。

门禁命令见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/validation.md`；测试分层见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/testing.md`。
