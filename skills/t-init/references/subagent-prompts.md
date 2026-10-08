# t-init Subagent Prompt 模板

主 Agent 在调度初始化角色时读取本文件，只取当前模式对应模板。全栈模式替换全部项目名占位符并附上 Step 2 的依赖版本；扩展 Demo 模式传入已核实的项目事实，不读取全栈模板。

## extension-demo-dev

```text
为当前已有 WXT 工程初始化 extension-demo 基础设施；不是用户故事实现任务。

目标项目根目录：[绝对路径]
扩展目录、包管理器和锁定版本：[实际值]
构建命令、工作目录和 MV3 产物目录：[实际值]
现有入口与最小可观察加载结果：[代码/配置来源]
宿主/stub 或真实后端依赖及环境模式：[已确认事实]
现有 Demo 配置、fixture 和需保留的测试：[路径或不存在]
官方 API 核对结果：[版本与查询结果]

读取 ${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/extension-demo-template.md，按目标工程适配模板，只生成或合并 Demo 配置、extension-target、fixture、helper 和 smoke。不修改扩展生产逻辑，不编造用户故事；本地 Python 脚本与根目录文档由主 Agent 处理。
安装 Demo 依赖和 Chromium，运行 Demo 类型检查、用例发现、扩展构建及最小加载测试；主 Agent 在本地脚本准备好后负责最终 runner 验证。返回 task_completion，明确修改文件、真实验证结果、缺口和失败证据，不把未执行标为成功。
```

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
   c. backend/.gitignore（忽略 target/ 和本地 config.toml）

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
- eslint.config.js（ESLint + @shadcn/lint 设计系统守卫；ui/ 目录须用块级 ignores 豁免）
- openapi-ts.config.ts
- index.html
- src/main.tsx（React Query + TanStack Router 初始化）
- src/styles.css（Tailwind v4 主题 + 暗色模式）
- src/routes/__root.tsx（根布局 + Toaster + DevTools）
- src/routes/index.tsx（首页）
- src/lib/api-client.ts（Axios 实例）
- src/routeTree.d.ts（类型声明占位）
- .gitignore（忽略 node_modules/、dist/、src/routeTree.gen.ts）

替换占位符：
- {{PROJECT_NAME}} → <实际项目名>
- {{PROJECT_NAME_PASCAL}} → <PascalCase>

## 阶段二：CLI 驱动的组件初始化

这些文件不要 AI 手写，必须通过 CLI 命令生成：

- npm install（安装所有依赖）
- npx shadcn@latest init -d --defaults
   - 自动生成 components.json、button.tsx、utils.ts，更新 styles.css
   - 自动安装额外依赖（@base-ui/react、next-themes 等）
   - components.json 生成后，@shadcn/lint 即可自动发现组件
- npx shadcn@latest add sonner --overwrite（生成 sonner.tsx）
   - 生成的 sonner.tsx 使用 next-themes，main.tsx 已包含 ThemeProvider
- npm run type-check 验证
- npm run lint 验证（@shadcn/lint 应 0 error；warning 需处理或在 eslint.config.js 契约中注明设计依据）

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
