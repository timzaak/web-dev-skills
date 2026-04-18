# Frontend 规范入口

frontend 规范入口，按“先定位问题，再读对应页面”使用。

| 你要确认的问题 | 对应规范 |
| --- | --- |
| 当前 frontend 架构事实、目录职责、路由与 API 约束 | [development.md](/guides/frontend/development.md) |
| Query / Router / Form / API / Tailwind 的项目常用模式 | [patterns.md](/guides/frontend/patterns.md) |
| Vitest、MSW、测试边界与测试写法 | [testing.md](/guides/frontend/testing.md) |
| 完成前最小验证命令与门禁 | [validation.md](/guides/frontend/validation.md) |
| 只读验收、API 一致性、Demo-first 测试合规 | [quality.md](/guides/frontend/quality.md) |
| `data-testid` 命名与覆盖范围 | [testid-standards.md](/guides/frontend/testid-standards.md) |

## 使用规则

- `development.md` 是 frontend 的事实型主规范，其他页面不应重复定义第二套架构真相。
- `patterns.md` 只记录本项目已采用的高频实现模式，不替代真实代码。
- `testing.md` 只负责测试 how-to，不负责重述全部架构。
- agent 文档只定义执行顺序、门禁和输出契约，不重新发明框架、路由或组件规范。
