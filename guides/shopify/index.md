# Shopify 规范入口

Shopify App 开发规范入口，按"先定位问题，再读对应页面"使用。适用于基于 Shopify 官方 React Router 模板的 Shopify App 项目（`shopify-app` 与 `shopify-extension` 两个 phase）。

技术基线：Shopify 官方 React Router 模板（React Router 7 framework mode，单工程承载服务端路由与 admin 嵌入页）/ Polaris / App Bridge / Prisma / theme app extension / customer account UI extension。不引入 TanStack Router/Query/Zustand 栈；店面 UI 是扩展内独立打包的前端资产，不是 React Router 页面。

| 你要确认的问题 | 对应规范 |
| --- | --- |
| 工程结构事实、admin 嵌入页、app proxy 验签、扩展交付面、CLI 工作流与部署时机 | [development.md](${CLAUDE_PLUGIN_ROOT}/guides/shopify/development.md) |
| Vitest 测试边界与店面 Demo 的分工 | [testing.md](${CLAUDE_PLUGIN_ROOT}/guides/shopify/testing.md) |
| 完成前最小验证命令与 `shopify app dev` 冒烟判定 | [validation.md](${CLAUDE_PLUGIN_ROOT}/guides/shopify/validation.md) |
| 只读验收关注点：验签、scopes、PII、扩展落位 | [quality.md](${CLAUDE_PLUGIN_ROOT}/guides/shopify/quality.md) |

## 使用规则

- `development.md` 是 Shopify 栈的事实型主规范；真实目录与脚本以目标项目现状为准，本规范只约束结构语义和跨项目稳定的行为。
- 官方 API 细节（扩展目标名、App Bridge 接口、验签算法）不在本规范复制；以 shopify.dev 文档和目标项目模板自带实现为准。
- agent 文档只定义执行顺序、门禁和输出契约，不重新定义架构真相。
