# Flutter 单元与 Widget 测试

保持大量快速的单元/widget 测试，用足够的 integration test 覆盖重要用例；demo-first 不替代快速测试。

## 选择测试层

| 类型 | 适用范围 | 默认命令 |
| --- | --- | --- |
| 单元测试 | service、repository、纯函数、Notifier/ViewModel | `flutter test test/<path>` |
| Widget 测试 | View、路由、依赖注入、表单和局部交互 | `flutter test test/<path>` |
| Integration | 重要用户用例、跨组件协同 | 见 `integration-testing.md` |
| Patrol/等价工具 | 权限、通知、WebView 等原生 UI | 见 `integration-testing.md` |

测可观察行为，不测私有方法或框架调用。fake 优先于基于调用次数的过度 mock；每个测试隔离数据和可变状态。

## Widget 测试

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

- `pump()` 推进帧；只在确实会稳定时使用 `pumpAndSettle()`。
- 无限动画使用定长 `pump` 或针对性同步条件。
- 禁止 `sleep` / `Future.delayed` 真实等待。
- finder 规则统一看 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/integration-testing.md`。

## Riverpod provider 测试

先读 `pubspec.lock`：

- Riverpod 3：`ProviderContainer.test()`，自动释放。
- Riverpod 2：`ProviderContainer()` + `addTearDown(container.dispose)`。
- 通过 `container.read(xxxProvider.notifier)` 驱动 Notifier，不直接构造脱离 provider 生命周期的 Notifier。

```dart
test('search returns users', () async {
  final container = ProviderContainer.test(overrides: [
    userRepositoryProvider.overrideWithValue(FakeUserRepo()),
  ]);

  final result = await container.read(userSearchProvider('ada').future);
  expect(result, isNotEmpty);
});
```

测试目录镜像 `lib/`，公共 fake/helper 分别放项目既有的 `test/fakes/`、`test/helpers/`。不要因已有 E2E 删除能快速定位失败或覆盖边界的测试。

演示测试见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/integration-testing.md`；验证命令见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/validation.md`。
