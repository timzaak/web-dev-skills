# Miniapp 规范入口

miniapp（微信小程序）规范入口，按"先定位问题，再读对应页面"使用。

| 你要确认的问题 | 对应规范 |
| --- | --- |
| 当前 miniapp 架构事实、目录职责、页面注册与主题约束 | [development.md](/guides/miniapp/development.md) |
| 类型检查、构建命令、门禁与测试 how-to | [testing.md](/guides/miniapp/testing.md) |
| 完成前最小验证命令与门禁 | [validation.md](/guides/miniapp/validation.md) |
| 只读验收、模板完整性、技术线合规 | [quality.md](/guides/miniapp/quality.md) |
| 受保护文件、禁用依赖、项目约束 | [ai-rules.md](/guides/miniapp/ai-rules.md) |
| Taro + Taroify + Tailwind 技术线约束真相 | [constitution.md](/guides/miniapp/constitution.md) |

## 使用规则

- `development.md` 是 miniapp 的事实型主规范，其他页面不应重复定义第二套架构真相。
- `constitution.md` 是技术线约束真相，agent 文档只引用不重写。
- `testing.md` 只负责测试与构建 how-to，不负责重述全部架构。
- agent 文档只定义执行顺序、门禁和输出契约，不重新发明框架、路由或组件规范。
