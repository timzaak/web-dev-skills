# t-init Subagent Prompt 模板

主 Agent 在调度 `backend-dev` / `frontend-dev` / `web-demo-dev` 时读取本文件，取对应模板，替换全部占位符（`{{PROJECT_NAME}}`、`{{PROJECT_NAME_PASCAL}}`、`{{PROJECT_NAME_SNAKE}}`），并附上 Step 2 收集的依赖版本信息。模板中的关键约束已固化，调度时不得省略。

## backend-dev

```text
初始化后端项目 {{PROJECT_NAME}}。

工作目录：<project-name>/backend/

任务：
- 读取后端模板文件 ${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/backend-template.md
- 按模板生成所有文件，替换以下占位符：
   - {{PROJECT_NAME}} → <实际项目名>
   - {{PROJECT_NAME_PASCAL}} → <PascalCase>
   - {{PROJECT_NAME_SNAKE}} → <snake_case>
- 注意目录名为 core/，Cargo crate 名为 {{PROJECT_NAME}}-core
- Rust 代码中使用 {{PROJECT_NAME_SNAKE}}_core:: 引用核心 crate
- 根据 Context7 查询结果调整依赖版本（版本信息：[附上 Step 2 收集的版本]）

- 生成构建和测试配置文件：
   a. backend/.cargo/config.toml（sccache 加速 + dev/release/test profile 优化）
   b. backend/.config/nextest.toml（nextest 测试运行器配置）

关键约束：
- sqlx::postgres::PgPoolOptions 没有 connect_timeout 方法，用 acquire_timeout 替代
- OpenAPI 开关：enable_openapi = true 时暴露 /swagger，否则返回 404
- 健康检查：GET /health 检查数据库和 Redis 连接
- 自动迁移：启动时运行 SQLx 迁移

完成后执行 cargo check 验证编译。
```

## frontend-dev

```text
初始化前端项目 {{PROJECT_NAME}}。

工作目录：<project-name>/frontend/

任务分两阶段：

## 阶段一：写入配置和自定义文件

读取前端模板文件 ${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/frontend-template.md，
生成以下自定义文件（需要 AI 编写的内容）：

必须由 AI 编写的文件（从模板生成）：
- package.json（含所有依赖）
- tsconfig.json
- vite.config.ts（Tailwind + TanStack Router + React 插件）
- openapi-ts.config.ts
- index.html
- src/main.tsx（React Query + TanStack Router 初始化）
- src/styles.css（Tailwind v4 主题 + 暗色模式）
- src/routes/__root.tsx（根布局 + Toaster + DevTools）
- src/routes/index.tsx（首页）
- src/lib/api-client.ts（Axios 实例）
- src/routeTree.d.ts（类型声明占位）

替换占位符：
- {{PROJECT_NAME}} → <实际项目名>
- {{PROJECT_NAME_PASCAL}} → <PascalCase>

## 阶段二：CLI 驱动的组件初始化

这些文件不要 AI 手写，必须通过 CLI 命令生成：

- npm install（安装所有依赖）
- npx shadcn@latest init -d --defaults
   - 自动生成 components.json、button.tsx、utils.ts，更新 styles.css
   - 自动安装额外依赖（@base-ui/react、next-themes 等）
- npx shadcn@latest add sonner --overwrite（生成 sonner.tsx）
   - 生成的 sonner.tsx 使用 next-themes，main.tsx 已包含 ThemeProvider
- npm run type-check 验证

注意：routeTree.gen.ts 在首次 npm run dev 时才会生成，type-check 可能因此报错，这是正常的。

关键约束：
- 每个关键文件都要有中文注释说明用途、技术选择、修改指南
- package.json 的 scripts 要有注释说明每个命令做什么
- 根据 Context7 查询结果调整依赖版本（版本信息：[附上 Step 2 收集的版本]）
```

## web-demo-dev

```text
初始化 Demo E2E 测试项目 {{PROJECT_NAME}}。

工作目录：<project-name>/demo/

任务：
- 读取 demo 模板文件 ${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/demo-template.md
- 按模板生成所有文件，替换占位符
- 生成后执行 npm install 安装依赖
- 运行 smoke test 验证 demo 环境正常

替换占位符：
- {{PROJECT_NAME}} → <实际项目名>
- {{PROJECT_NAME_PASCAL}} → <PascalCase>
- {{BASE_URL}} → http://localhost:8080

必须包含的 smoke test（smoke.e2e.ts）：
- 不依赖后端服务
- 验证 Playwright 能启动浏览器
- 验证页面导航基本功能
- 验证测试基础设施（fixtures、helpers）可正常导入
- 这个测试必须在 npm install 后立即可运行通过

完成后执行 cd demo && npx playwright install chromium && npx playwright test e2e/smoke.e2e.ts
确保 smoke test 全部通过。
```
