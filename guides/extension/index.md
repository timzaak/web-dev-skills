# Extension 规范入口

Chrome 扩展（Manifest V3）规范入口，按“先定位问题，再读对应页面”使用。技术基线基于 frontend Web 栈（React + TypeScript + Vite 系），构建层使用 WXT。

| 你要确认的问题 | 对应规范 |
| --- | --- |
| 默认技术基线、上下文边界、消息与存储实践 | [development.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/development.md) |
| Vitest/MSW 测试边界、fakeBrowser 用法与 Playwright 扩展 E2E | [testing.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/testing.md) |
| 完成前最小验证命令与门禁 | [validation.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/validation.md) |
| 只读验收、权限最小化、契约一致性检查 | [quality.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/quality.md) |

## 使用规则

- `development.md` 维护 extension 工程基线；项目代码/配置是当前实现事实，跨阶段输出和验收判定由 protocols 定义。
- 与 frontend 共享的实践（Vitest 测试原则、`data-testid`、Query/Zod/Tailwind 模式）以 `guides/frontend/` 对应页面为准，本目录只维护插件特有差异。
- `testing.md` 只负责测试 how-to，不负责重述全部架构。
- agent 文档只定义执行顺序、门禁和输出契约，不重新发明框架、入口或契约规范。
