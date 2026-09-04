# t-init Subagent Prompt 模板

主 Agent 在调度 `backend-dev` / `frontend-dev` / `web-demo-dev` 时读取本文件，取对应模板，替换全部占位符（`{{PROJECT_NAME}}`、`{{PROJECT_NAME_PASCAL}}`、`{{PROJECT_NAME_SNAKE}}`、`{{PROJECT_PACKAGE}}`、`{{PROJECT_PACKAGE_PATH}}`），并附上 Step 2 收集的依赖版本信息。模板中的关键约束已固化，调度时不得省略。

## backend-dev

```text
初始化后端项目 {{PROJECT_NAME}}。

工作目录：<project-name>/backend/

任务：
- 读取后端模板文件 ${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/backend-template.md
- 按模板生成所有 Spring Boot 文件，替换以下占位符：
   - {{PROJECT_NAME}} → <实际项目名>
   - {{PROJECT_NAME_PASCAL}} → <PascalCase>
   - {{PROJECT_NAME_SNAKE}} → <snake_case>
   - {{PROJECT_PACKAGE}} → <Java package，默认 com.example.<snake 去下划线>>
   - {{PROJECT_PACKAGE_PATH}} → <package 路径，如 com/example/myproject>
- 默认使用 Maven 项目结构
- 根据 Context7 查询结果调整依赖版本（版本信息：[附上 Step 2 收集的版本]）

关键约束：
- Java 版本基线为 17（Spring Boot 3 最低基线）；目标环境明确使用 Java 21 时可修改 java.version
- OpenAPI 使用 springdoc：运行后暴露 /v3/api-docs 与 /swagger-ui.html
- 健康检查：GET /health 是给前端/demo 脚本的兼容入口，生产监控优先使用 Actuator /actuator/health
- 统一错误响应入口（ApiErrorHandler），覆盖校验失败和通用异常
- 新增业务模块时先遵循目标项目真实包结构，不强制套 controller/service/repository 目录

完成后执行 cd backend && mvn test 验证。
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
