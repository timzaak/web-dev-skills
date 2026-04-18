# 前端开发规范

当前 frontend 的事实型主规范。只描述仓库现状、稳定约束和最低验证，不承担 React、TanStack 或 Zod 的教学职责。

## 1. 文档定位

本页保留：
- 当前 frontend 的技术基线、目录职责和路由事实
- 数据访问、生成代码、组件复用的稳定约束
- 完成前最低验证命令

本页不展开：
- Vitest、MSW、测试写法细节
- 长篇 Router / Form / Zod / Table 教学示例
- 某个 feature 的局部实现 recipe

相关入口：
- frontend 规范入口：`./index.md`
- 测试规则：`./testing.md`
- 完成前验证：`../agents/frontend/validation.md`
- 验收与 Demo-first 要求：`../agents/frontend/quality.md`
- `data-testid` 规则：`../agents/frontend/testid-standards.md`

## 2. 当前技术基线

`frontend/package.json` 当前可确认的主栈：

- React 19
- TypeScript 5
- Vite 7
- TanStack Router
- TanStack Query
- TanStack Form
- Zod 4
- Tailwind CSS 4
- Radix UI
- Vitest + Testing Library + MSW
- `@hey-api/openapi-ts` 生成的 API 客户端

补充事实：
- `npm run build` 当前执行 `vite build && tsc --noEmit`。

## 3. 当前目录与职责

以 `frontend/src/` 当前实现为准：

| 路径 | 当前职责 |
| --- | --- |
| `routes/` | 页面路由入口与路由树节点 |
| `components/` | 页面组件、共享 UI、业务组件 |
| `data/` | 查询参数与数据访问辅助 |
| `hooks/` | 页面相关状态与复用逻辑 |
| `lib/` | 工具函数、query provider、生成的 API 客户端 |
| `stores/` | 全局状态 |
| `test/` / `tests/` | Vitest 初始化、mocks 和测试代码 |

生成代码目录 `frontend/src/lib/api-generated/` 视为派生物，不手工维护业务逻辑。

## 4. 路由与页面事实

稳定事实：
- 路由真相以 `frontend/src/routes/` 和 `frontend/src/routeTree.gen.ts` 为准。
- 新页面优先遵循当前文件路由结构和现有路由分组方式。
- 当前默认使用固定单租户路径，如 `/auth/login`、`/manage`、`/manage/users`。
- 不要把历史文档里的旧租户前缀路由当作默认事实。

## 5. 数据访问与组件约束

- API 类型和客户端调用优先复用 `frontend/src/lib/api-generated/`。
- API 契约变化后，先刷新 OpenAPI 生成物，再继续写页面逻辑。
- 页面级查询与缓存行为优先复用现有 QueryClient 配置、query options 和 hooks。
- 优先复用 `components/ui/` 与已有共享组件；不要为一次性页面逻辑平行造一套全局框架。
- `data-testid` 命名与覆盖范围只看专项规范，不在本页重复定义。

## 6. 当前实现边界

以下内容不再视为 frontend 主规范的默认事实：

- 任何带租户前缀的旧模板路由是默认路由架构
- 主指南内保留完整 TanStack Router / Form / Zod 教学
- 所有表单都必须走同一套全局样板组件
- 长代码示例可以替代仓库真实实现

如某个 feature 需要特殊表单模式、OAuth 处理或局部路由技巧，应写到该 feature 设计文档、测试文档或具体实现附近，而不是回写成 frontend 全局主规范。

## 7. 完成前最低验证

```bash
cd frontend
npm run type-check
npm run build
```

如需更完整门禁、Vitest 范围或 Demo-first 验收，按 `./testing.md`、`../agents/frontend/validation.md` 和 `../agents/frontend/quality.md` 执行。
