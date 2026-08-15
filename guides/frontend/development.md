# 前端开发规范

Frontend 主规范。它定义插件级稳定约束；目标项目的真实路由、目录职责、组件体系和依赖版本以目标项目代码与 `docs/`、`.ai/` 产物为准。

## 1. 文档定位

本页保留：
- frontend 技术基线、目录职责和路由事实的确认方法
- 数据访问、生成代码、组件复用的稳定约束
- 完成前最低验证命令

本页不展开：
- Vitest、MSW、测试写法细节
- 长篇 Router / Form / Zod / Table 教学示例
- 某个 feature 的局部实现 recipe

相关入口：
- frontend 规范入口：`./index.md`
- 测试规则：`./testing.md`
- 完成前验证：`${CLAUDE_PLUGIN_ROOT}/guides/frontend/validation.md`
- 验收与 Demo-first 要求：`${CLAUDE_PLUGIN_ROOT}/guides/frontend/quality.md`
- `data-testid` 规则：`${CLAUDE_PLUGIN_ROOT}/guides/frontend/testid-standards.md`

## 2. 当前技术基线

先读取目标项目的 `frontend/package.json`、路由入口、API 客户端生成配置和现有页面代码，确认真实技术栈。默认模板倾向以下组合，但不得覆盖目标项目事实：

- React
- TypeScript
- Vite
- TanStack Router
- TanStack Query
- TanStack Form
- Zustand（客户端/UI 状态）
- Zod
- Tailwind CSS
- Radix UI
- Vitest + Testing Library + MSW
- `@hey-api/openapi-ts` 生成的 API 客户端

构建、类型检查和测试命令以 `frontend/package.json` scripts 为准。

## 3. 当前目录与职责

以目标项目 `frontend/src/` 当前实现为准。先确认路由、组件、hooks、数据访问、测试初始化和生成代码目录的实际落点，再写入或修改文件。生成代码目录视为派生物，不手工维护业务逻辑。

## 4. 路由与页面事实

稳定事实：
- 路由真相以目标项目当前路由文件、路由生成物和路由配置为准。
- 新页面优先遵循当前文件路由结构和现有路由分组方式。
- 不要把历史文档里的旧路径、固定管理路径或示例路由当作默认事实。

## 5. 数据访问与组件约束

- API 类型和客户端调用优先复用目标项目现有生成目录。
- API 契约变化后，先刷新 OpenAPI 生成物，再继续写页面逻辑。
- 页面级查询与缓存行为优先复用现有 QueryClient 配置、query options 和 hooks。
- 状态分工：服务端数据（查询、缓存、失效、重新获取）由 TanStack Query 独占管理，只存在于 Query 缓存中，不进入 Zustand。Zustand 只承载全局客户端/UI 状态（开关、草稿、跨页面交互状态）。需要跨组件记住某条服务端数据的选中态时，在 Zustand 存 ID 引用，不复制数据对象。组件通过 selector 订阅最小所需状态，订阅对象/数组时做浅比较。
- 优先复用 `components/ui/` 与已有共享组件；不要为一次性页面逻辑平行造一套全局框架。
- `data-testid` 命名与覆盖范围只看专项规范，不在本页重复定义。

## 6. 当前实现边界

以下内容不再视为 frontend 主规范的默认事实：

- 任何旧模板路由是默认路由架构
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

如需更完整门禁、Vitest 范围或 Demo-first 验收，按 `./testing.md`、`${CLAUDE_PLUGIN_ROOT}/guides/frontend/validation.md` 和 `${CLAUDE_PLUGIN_ROOT}/guides/frontend/quality.md` 执行。
