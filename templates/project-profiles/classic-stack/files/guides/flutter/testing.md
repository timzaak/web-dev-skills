# Flutter 单元与 Widget 测试

用户故事主链路优先由 Flutter Demo 或集成测试覆盖。仅当这些测试难以稳定覆盖重要业务规则、状态转换或异常边界时，才补少量定向单元/widget 测试；不按数量或目录结构补测试。受影响的现有测试仍需定向运行。

## 选择测试层

| 类型 | 适用范围 | 默认命令 |
| --- | --- | --- |
| 单元测试（按需） | Demo/集成测试难稳定覆盖的 service、repository、纯函数、Notifier/ViewModel 关键规则 | `flutter test test/<path>` |
| Widget 测试（按需） | Demo/集成测试难稳定覆盖的 View、路由、依赖注入、表单关键状态 | `flutter test test/<path>` |
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

确需新增局部测试时沿用项目既有目录；公共 fake/helper 放项目既有的 `test/fakes/`、`test/helpers/`。不要仅因已有 Demo 删除能快速定位失败或覆盖关键边界的测试。

普通集成测试见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/integration-testing.md`；用户故事演示见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/demo-testing.md`；验证命令见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/validation.md`。
