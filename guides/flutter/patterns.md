# Flutter 常用模式

先复用目标项目现有 widget、provider 和 helper；示例只表达规则。

## Widget

- 优先 `StatelessWidget`；纯局部交互状态才用 `StatefulWidget`。
- 能用 `const` 就用；按职责和状态变化边界拆分，不设机械行数门槛。
- `build()` 不做 IO、副作用或昂贵重复计算。

## Riverpod

- `ref.watch` 订阅，事件中 `ref.read`，副作用用事件回调/`ref.listen`。
- 异步状态用 `AsyncValue`；用户错误映射为本地化消息，不显示原始异常。

```dart
final users = ref.watch(userListProvider);
return users.when(
  data: (items) => UserList(items: items),
  loading: () => const CircularProgressIndicator(),
  error: (_, _) => Text(context.l10n.loadFailed),
);
```

可修改异步状态用 `AsyncNotifier`；只读异步读取用 `FutureProvider`。重试保留原始参数：

```dart
@riverpod
class UserSearch extends _$UserSearch {
  @override
  Future<List<User>> build(String keyword) =>
      ref.read(userRepositoryProvider).search(keyword);

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref.read(userRepositoryProvider).search(keyword),
    );
  }
}
```

## 表单

校验用 `FormField.validator`；文案本地化、视觉样式主题化。提交/loading/error 状态集中管理。

```dart
TextFormField(
  decoration: InputDecoration(labelText: context.l10n.emailLabel),
  validator: (value) {
    if (value == null || value.isEmpty) return context.l10n.emailRequired;
    return value.contains('@') ? null : context.l10n.emailInvalid;
  },
)
```

## 路由

- 复用项目当前 go_router/typed route 结构。
- 守卫集中处理；多导航栈使用 `ShellRoute`/`StatefulShellRoute`。
- 认证状态必须能触发路由刷新；不要引用作用域外的 `ref`，也不要无条件重建 `GoRouter`。

```dart
final router = GoRouter(routes: [
  GoRoute(path: '/users', builder: (_, _) => const UserListPage()),
  GoRoute(path: '/settings', builder: (_, _) => const SettingsPage()),
]);
```

状态技术线见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/constitution.md`；架构边界见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/development.md`。
