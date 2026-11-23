# Flutter 单元、Widget 与集成测试指南

用户故事主链路优先由 Flutter Demo（见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/demo-testing.md`）或集成测试覆盖。仅当这些测试难以稳定覆盖重要业务规则、状态转换或异常边界时，才补少量定向单元/widget 测试；不按数量或目录结构补测试。受影响的现有测试仍需定向运行。

## 1. 测试分层

| 类型 | 适用范围 | 默认命令 |
| --- | --- | --- |
| 单元测试（按需） | Demo/集成测试难稳定覆盖的 service、repository、纯函数、Notifier/ViewModel 关键规则 | `flutter test test/<path>` |
| Widget 测试（按需） | Demo/集成测试难稳定覆盖的 View、路由、依赖注入、表单关键状态 | `flutter test test/<path>` |
| Integration | 重要用户用例、跨组件协同（Android/iOS/desktop/Web） | `flutter test integration_test/<file> -d <device-id>` |
| Patrol（原生 UI） | 权限、通知、WebView、应用切换等原生 UI | `patrol test --target patrol_test/<file> --device <device-id>` |

测可观察行为，不测私有方法或框架调用。fake 优先于基于调用次数的过度 mock；每个测试隔离数据和可变状态。不要仅因已有 Demo 删除能快速定位失败或覆盖关键边界的测试。

## 2. Widget 与 Riverpod Provider 测试

用 `MaterialApp` 和 `ProviderScope` 提供必要上下文，通过 override 注入 fake：

```dart
Future<void> pumpPage(WidgetTester tester, {List<Override> overrides = const []}) {
  return tester.pumpWidget(
    ProviderScope(
      overrides: overrides,
      child: const MaterialApp(home: UserListPage()),
    ),
  );
}
```

- `pump()` 推进帧；只在确实会稳定时使用 `pumpAndSettle()`；无限动画使用定长 `pump` 或针对性同步条件；禁止 `sleep` / `Future.delayed` 真实等待。
- Riverpod provider 测试先读 `pubspec.lock`：Riverpod 3 用 `ProviderContainer.test()`（自动释放）；Riverpod 2 用 `ProviderContainer()` + `addTearDown(container.dispose)`；通过 `container.read(xxxProvider.notifier)` 驱动 Notifier，不直接构造脱离 provider 生命周期的 Notifier。

```dart
test('search returns users', () async {
  final container = ProviderContainer.test(overrides: [
    userRepositoryProvider.overrideWithValue(FakeUserRepo()),
  ]);

  final result = await container.read(userSearchProvider('ada').future);
  expect(result, isNotEmpty);
});
```

确需新增局部测试时沿用项目既有目录；公共 fake/helper 放项目既有的 `test/fakes/`、`test/helpers/`。

## 3. 集成测试与 Finder 规则

### 载体与命令

- Android、iOS、desktop：官方 `integration_test`。
- Web：使用 `integration_test` + 匹配版本的 ChromeDriver、driver 文件与 `flutter drive`。
- 原生 UI（权限弹窗、通知、WebView、应用切换）：目标项目已采用 Patrol 时使用 Patrol，否则在设计中指定等价方案。用户故事演示使用 `flutter-demo` phase 和 `patrol_test/`，不混入普通 `flutter/test` runner。

```bash
flutter devices
flutter test integration_test/login_flow_test.dart -d <device-id>

# Web
flutter drive \
  --driver=test_driver/integration_test.dart \
  --target=integration_test/login_flow_test.dart \
  -d chrome
```

CI 记录设备、OS、Flutter 版本和实际命令。只有真实硬件能力或模拟器无法复现的流程才强制真机。

### Finder 与 Key 集中管理

优先级：稳定 Key > Semantics label > 稳定文案 > icon/type。禁止依赖 widget 树位置或深层 `find.descendant`。关键交互控件使用 `ValueKey('<domain>-<entity>-<action|field>')`（如 `login-email-input`），动态列表项用稳定业务 ID，装饰性控件不加测试 Key。

测试与 Widget 共用的 Key 字符串集中在单一文件（如 `integration_test_keys.dart`），按页面分组：

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

主链路存在多个用例复用时，将 finder/动作提取到 `integration_test/screens/`，断言留在测试文件；不为单个短用例强制创建 Screen Object。

## 4. Patrol 4 基础与门禁

首次接入或排查原生 runner 时遵循 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/demo-testing.md` 的 Patrol 初始化节；先读目标项目 `pubspec.lock` 按官方兼容表选 `patrol_cli`，不自动升级。

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

- Patrol UI 测试不能用普通 `flutter test`；跨 Android/iOS 的原生移动端动作优先使用 `$.platform.mobile`，平台专属才用 `$.platform.android` / `$.platform.ios`，Web 用 `$.platform.web`。
- 门禁：改动影响重要用户用例时运行对应 integration test；原生 UI 流程提供 Patrol 或等价自动化证据；不使用 `sleep`/真实延迟，不放宽断言绕过失败。

验证命令与验收判定见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/quality.md`。
