# Flutter 开发规范

目标项目代码、`pubspec.yaml`、`pubspec.lock`、`analysis_options.yaml` 是版本、目录和依赖真相；本页只定义稳定边界。

## 技术与架构

默认倾向 Flutter stable、Material 3、go_router、Riverpod、dio、freezed/json_serializable；项目事实优先。

- UI：View 负责渲染、布局、动画和简单导航；Notifier/AsyncNotifier 承担 ViewModel 等价职责。
- Data：Repository 是一类应用数据的真相来源；Service 封装 HTTP、存储和平台插件。
- Domain：仅在复杂或重复业务逻辑挤占多个 Notifier 时引入。
- 依赖方向：View -> Notifier -> Repository -> Service；provider 负责依赖注入。
- 数据流：事件向下、状态向上；模型优先不可变，View 不直接修改数据源。

- 旧项目渐进收敛，不做无收益重写。

## 目录与路由

先识别现有骨架，再沿用：

- `lib/main.dart` / `lib/app.dart`：启动和根装配。
- `lib/core/`：跨 feature 基础设施。
- `lib/features/<domain>/`：页面、widget、provider、model 等领域代码。
- `lib/router/`：路由表与守卫。

生成文件是派生物，不手工维护。路由优先复用项目现有 go_router/typed route 方案；不要从历史文档推断路径，也不要为简单跳转强行重写稳定导航。

## API 客户端

- 目标项目已有 API client 生成流程时，先确认其配置、输入和输出位置，并优先复用生成的 client/type。
- API 契约变化后，先再生客户端，再调整 Repository、Service、Notifier 和 View；生成物不手工编辑。
- 未采用 API client 生成的项目不强制引入新的生成工具或独立 package。

## UI 质量

- 设计值走 `ThemeData`、`ColorScheme`、`ThemeExtension`。
- 用可用空间而非设备型号做响应式布局；覆盖目标平台键鼠、焦点和触摸输入。
- 用户文案走本地化；自定义交互补齐 Semantics 与可访问名称。
- 不在 `build()` 做 IO 或昂贵重复计算；大列表惰性构建。
- 性能结论来自 profile mode、DevTools/时间线或 performance test，不凭 debug 观感猜测。

## 实现边界

- 复用现有 client、repository、共享 widget 和错误模型。
- 状态规则见 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/constitution.md`。
- 平台代码、权限和通道仅在必要时修改，并写入 Handoff。
- 完成前按 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/validation.md` 验证。
