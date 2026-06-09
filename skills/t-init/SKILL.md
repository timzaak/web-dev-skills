---
name: t-init
description: Initialize a full-stack project skeleton with Rust backend (Axum + SeaORM + Redis) and React frontend (TypeScript + TanStack + Tailwind).
argument-hint: "<project-name>"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
  - Bash
  - Agent
  - WebSearch
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
---

# 项目初始化

初始化一个全栈项目骨架：Rust 后端 (Axum + Sea-ORM + Redis) + React 前端 (TypeScript + TanStack + Tailwind)。

## 适用范围

仅在以下场景使用：
- 用户明确执行 `/t-init <project-name>`
- 用户要求创建新项目、初始化全栈项目骨架
- 用户提到 "搭建项目""新建项目""项目初始化"

不要用于：
- 已有项目的增量开发
- 代码修改或重构
- 单纯的前端或后端初始化（如果明确只做一侧，提示用户本 skill 生成完整全栈）

## 参数

- `$ARGUMENTS` = 项目名称（必须）
- 仅允许英文、数字、连字符、下划线
- 拒绝 `..`、`/`、`\`
- 长度限制 1-50 字符

如果参数不合法，终止并提示：
`请提供合法的项目名称。例如：/t-init my-project`

## 占位符

整个流程中使用以下占位符：

- `{{PROJECT_NAME}}` — 项目名称（kebab-case，如 `my-project`）
- `{{PROJECT_NAME_PASCAL}}` — PascalCase（如 `MyProject`）
- `{{PROJECT_NAME_SNAKE}}` — snake_case（如 `my_project`）

## 生成流程

### Step 1: 验证参数（主 Agent）

- 校验 `$ARGUMENTS` 非空且合法
- 检查目标目录是否已存在同名目录
- 如果目录已存在且非空，询问用户是否覆盖
- 创建所有目录结构：

```
<project-name>/
├── backend/
│   ├── .cargo/
│   │   └── config.toml
│   ├── .config/
│   │   └── nextest.toml
│   ├── core/
│   │   └── src/
│   │       ├── domain/
│   │       └── infrastructure/
│   ├── api/
│   │   └── src/
│   │       └── application/
│   │           └── http/
│   ├── app/
│   │   └── src/
│   └── migrations/
├── frontend/
│   └── src/
│       ├── routes/
│       ├── components/ui/
│       └── lib/
├── demo/
│   └── e2e/
│       ├── fixtures/
│       ├── helpers/
│       └── pages/
└── scripts/
    └── lib/
```

### Step 2: 查询文档（主 Agent）

使用 Context7 查询关键依赖的最新文档，确保生成的代码使用当前最佳实践。

### 必查依赖（按顺序）

- **Axum** — 路由、状态共享、中间件写法
   - `mcp__context7__resolve-library-id` → query: "axum web framework"
   - `mcp__context7__query-docs` → query: "router, state sharing, middleware, serve static files"

- **Sea-ORM** — 数据库连接和实体定义
   - `mcp__context7__resolve-library-id` → query: "sea-orm rust database"
   - `mcp__context7__query-docs` → query: "database connection, entity generation, migration"

- **utoipa** — OpenAPI 文档生成
   - `mcp__context7__resolve-library-id` → query: "utoipa rust openapi"
   - `mcp__context7__query-docs` → query: "OpenApi derive, swagger ui, axum integration"

- **TanStack Router** — 前端文件路由
   - `mcp__context7__resolve-library-id` → query: "tanstack router react"
   - `mcp__context7__query-docs` → query: "file-based routing setup, vite plugin, createRouter"

- **TanStack Query** — 数据请求
   - `mcp__context7__resolve-library-id` → query: "tanstack query react"
   - `mcp__context7__query-docs` → query: "QueryClient setup, useQuery, QueryClientProvider"

如果某个 Context7 查询失败，降级到 `WebSearch` 搜索官方文档。如果都无法获取，基于已有知识生成但标注可能需要调整版本。

将查询结果中的版本号和 API 用法保存，传递给后续 subagent。

### Step 3: 生成后端（backend-dev subagent）

使用 Agent 工具调度 `t-tools:backend-dev` subagent。

**Subagent Prompt 模板**：

```
初始化后端项目 {{PROJECT_NAME}}。

工作目录：<project-name>/backend/

任务：
- 读取后端模板文件 C:\code\ai\skills\skills\t-init\references\backend-template.md
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

后端关键特性：
- **OpenAPI 开关**：通过 `config.toml` 中的 `server.enable_openapi` 控制
- **健康检查**：`GET /health` 检查数据库和 Redis 连接
- **自动迁移**：启动时自动运行 SQLx 迁移
- **静态文件服务**：开发环境可代理前端，生产环境从 `static_dir` 提供前端文件

### Step 4: 生成前端（frontend-dev subagent）

使用 Agent 工具调度 `t-tools:frontend-dev` subagent。

**Subagent Prompt 模板**：

```
初始化前端项目 {{PROJECT_NAME}}。

工作目录：<project-name>/frontend/

任务分两阶段：

## 阶段一：写入配置和自定义文件

读取前端模板文件 C:\code\ai\skills\skills\t-init\references\frontend-template.md，
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

前端文件要求：
- **代码注释**：每个关键文件都要有注释，解释用途、技术选择、修改指南
- 路由文件 (`__root.tsx`) 要有注释说明文件路由的工作方式
- `main.tsx` 要有注释说明 React 应用启动流程
- `vite.config.ts` 要有注释说明每个插件的作用
- **UI 组件（sonner 等）不要 AI 手写**，必须通过 `npx shadcn@latest add` 生成

### Step 5: 生成 Demo E2E 测试（demo-dev subagent）

使用 Agent 工具调度 `t-tools:demo-dev` subagent。

**Subagent Prompt 模板**：

```
初始化 Demo E2E 测试项目 {{PROJECT_NAME}}。

工作目录：<project-name>/demo/

任务：
- 读取 demo 模板文件 C:\code\ai\skills\skills\t-init\references\demo-template.md
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

### Step 6: 生成项目本地 scripts（主 Agent）

将插件运行时脚本复制到目标项目根目录 `scripts/`，作为该项目后续环境启动、测试执行和 Demo 运行的优先入口。

复制来源：`${CLAUDE_PLUGIN_ROOT}/scripts/`

必须复制：
- `backend-test.py`
- `test-start.py`
- `test-stop.py`
- `demo-start.py`
- `demo-stop.py`
- `demo-test-runner.py`
- `demo-run-all.py`
- `debug-test.py`
- `cleanup-demo.py`
- `cleanup-test-logs.py`
- `demo-failure-summary.py`
- `lib/*.py`

复制后按当前项目调整脚本默认配置：
- Docker 镜像、容器名和端口必须使用当前项目语义，避免多个初始化项目互相冲突。
- 默认数据库名、Redis 端口、后端/前端启动命令应与本次生成的 `backend/`、`frontend/`、`demo/` 保持一致。
- 脚本文件名、主要 CLI 参数和输出 JSON/日志契约保持稳定，便于 `/t-tools:t-*` 流程复用。
- 运行类命令优先使用 `uv run scripts/<name>.py`；只有目标项目缺少对应脚本时，才回退到 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py`。

### Step 7: 生成 AGENTS.md、CLAUDE.md 和 README.md（主 Agent）

读取 [references/agents-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/agents-template.md) 获取模板内容。

生成三个根目录文件：
- `AGENTS.md` — 项目描述占位符 + 项目行为准则
- `CLAUDE.md` — 仅包含 `@AGENTS.md`
- `README.md` — 快速启动指南（从 [references/scripts-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/scripts-template.md) 获取项目本地脚本命令）

生成后提示用户填写 `AGENTS.md` 顶部的项目描述占位符。

### Step 8: 验证（主 Agent）

收集各 subagent 的验证结果，汇总报告：
- 后端：`cargo check` 是否通过
- 前端：`npm install` + `type-check` 是否通过（routeTree.gen.ts 错误除外）
- Demo：`npm install` + smoke test 是否通过
- 检查所有文件都已创建（Glob 验证）

如果验证工具不可用，跳过并提示用户手动验证。

## 项目结构

生成的项目结构如下：

```
<project-name>/
├── backend/
│   ├── Cargo.toml              # Workspace 根配置
│   ├── .cargo/config.toml      # Cargo 构建优化（sccache、profile）
│   ├── .config/nextest.toml    # Nextest 测试运行器配置
│   ├── config.example.toml      # 配置模板
│   ├── migrations/              # SQLx 数据库迁移
│   │   └── 00001_init.sql
│   ├── core/                    # 领域核心（crate: {{PROJECT_NAME}}-core）
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── config.rs
│   │       ├── domain/
│   │       │   └── health.rs
│   │       └── infrastructure/
│   │           └── redis.rs
│   ├── api/
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── config.rs
│   │       └── application/
│   │           └── http/
│   │               ├── mod.rs
│   │               ├── handlers.rs
│   │               ├── openapi.rs
│   │               ├── routes.rs
│   │               └── state.rs
│   └── app/
│       ├── Cargo.toml
│       └── src/
│           └── main.rs
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── openapi-ts.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── styles.css
│       ├── routes/
│       │   ├── __root.tsx
│       │   └── index.tsx
│       ├── components/
│       │   └── ui/
│       │       └── sonner.tsx      # 由 npx shadcn add sonner 生成
│       ├── lib/
│       │   └── api-client.ts
│       └── routeTree.d.ts
├── demo/
│   ├── package.json             # 依赖 playwright-unified-logger
│   ├── tsconfig.json
│   ├── playwright.config.ts
│   ├── eslint.config.js
│   ├── .gitignore
│   └── e2e/
│       ├── smoke.e2e.ts          # 冒烟测试（不依赖后端）
│       ├── demo-basic.e2e.ts     # 基础验证测试
│       ├── fixtures/
│       │   ├── demo-auth.fixtures.ts
│       │   └── test-data.ts
│       ├── helpers/
│       │   ├── auth.ts
│       │   └── environment-setup.ts
│       ├── pages/
│       │   ├── base-page.ts
│       │   └── login-page.ts
│       └── selectors.ts
├── scripts/
│   ├── backend-test.py
│   ├── test-start.py
│   ├── test-stop.py
│   ├── demo-test-runner.py
│   ├── demo-run-all.py
│   └── lib/
├── AGENTS.md                    # Claude Code 行为准则 + 项目描述
├── CLAUDE.md                    # 引用 AGENTS.md
└── README.md
```

## 输出文件清单

完成后确认以下文件存在：

**后端（必须）：**
- [ ] `backend/Cargo.toml`
- [ ] `backend/.cargo/config.toml`
- [ ] `backend/.config/nextest.toml`
- [ ] `backend/core/Cargo.toml` + `src/lib.rs` + `src/config.rs` + `src/domain/health.rs` + `src/infrastructure/redis.rs`
- [ ] `backend/api/Cargo.toml` + `src/lib.rs` + `src/config.rs` + `src/application/http/*.rs`
- [ ] `backend/app/Cargo.toml` + `src/main.rs`
- [ ] `backend/config.example.toml`
- [ ] `backend/migrations/00001_init.sql`

**前端（必须）：**
- [ ] `frontend/package.json`
- [ ] `frontend/tsconfig.json`
- [ ] `frontend/vite.config.ts`
- [ ] `frontend/openapi-ts.config.ts`
- [ ] `frontend/index.html`
- [ ] `frontend/src/main.tsx`
- [ ] `frontend/src/styles.css`
- [ ] `frontend/src/routes/__root.tsx`
- [ ] `frontend/src/routes/index.tsx`
- [ ] `frontend/src/components/ui/sonner.tsx`（由 shadcn CLI 生成）
- [ ] `frontend/src/lib/api-client.ts`

**脚本和文档：**
- [ ] `scripts/backend-test.py`
- [ ] `scripts/test-start.py`
- [ ] `scripts/test-stop.py`
- [ ] `scripts/demo-test-runner.py`
- [ ] `scripts/demo-run-all.py`
- [ ] `scripts/demo-start.py`
- [ ] `scripts/demo-stop.py`
- [ ] `scripts/lib/*.py`
- [ ] `README.md`

**AI 辅助配置（必须）：**
- [ ] `AGENTS.md`
- [ ] `CLAUDE.md`

**Demo E2E 测试（必须）：**
- [ ] `demo/package.json`
- [ ] `demo/tsconfig.json`
- [ ] `demo/playwright.config.ts`
- [ ] `demo/eslint.config.js`
- [ ] `demo/.gitignore`
- [ ] `demo/e2e/smoke.e2e.ts`（冒烟测试，不依赖后端）
- [ ] `demo/e2e/demo-basic.e2e.ts`
- [ ] `demo/e2e/fixtures/demo-auth.fixtures.ts`
- [ ] `demo/e2e/fixtures/test-data.ts`
- [ ] `demo/e2e/helpers/auth.ts`
- [ ] `demo/e2e/helpers/environment-setup.ts`
- [ ] `demo/e2e/pages/base-page.ts`
- [ ] `demo/e2e/pages/login-page.ts`
- [ ] `demo/e2e/selectors.ts`

## 收尾输出

完成后在响应中明确说明：
- 项目路径
- 已生成的文件数量
- 各 subagent 验证结果（cargo check / npm install / smoke test）
- OpenAPI 开关位置（`config.toml` → `server.enable_openapi`）
- UnifiedLogger 通过 `npm install playwright-unified-logger` 安装
- 项目本地脚本已生成到 `scripts/`，后续优先执行 `uv run scripts/<name>.py`
- Demo smoke test 运行命令（`cd demo && npx playwright test e2e/smoke.e2e.ts`）
- 日志环境变量说明（`UNIFIED_LOG_LEVEL` 等）
- AGENTS.md 和 CLAUDE.md 已生成，提醒用户填写项目描述
- 快速启动命令
- 需要用户手动完成的步骤（如复制 config、安装 Docker 等）
- 下一步建议（如 `/t-prd` 开始功能规划）

## 质量门禁

生成前逐项自检：
- 是否查询了 Context7 确认依赖版本和用法
- 后端目录名为 `core/`，crate 名为 `{{PROJECT_NAME}}-core`，Rust 代码用 `{{PROJECT_NAME_SNAKE}}_core::`
- 后端 `.cargo/config.toml` 是否已生成（sccache + profile 优化）
- 后端 `.config/nextest.toml` 是否已生成（测试运行器配置）
- 后端 OpenAPI 开关逻辑是否正确（enable_openapi 控制路由注册）
- 后端是否能编译通过（`cargo check`）
- 前端 sonner 等组件是否通过 CLI 命令生成（不是 AI 手写）
- 前端代码是否有足够的中文注释
- demo smoke test 是否不依赖后端且能独立运行通过
- demo 中 import 路径是否正确指向 `playwright-unified-logger`（npm 包）
- 配置文件是否有完整的注释说明每个字段
- 所有占位符是否已替换为实际项目名称

## 失败处理

- 参数缺失或非法：终止并给出 `/t-init <project-name>` 示例
- 目标目录已存在且非空：询问是否覆盖
- Context7 查询失败：降级到 WebSearch，最终降级到已有知识
- cargo/npm 不可用：生成文件但跳过验证，提示用户手动检查
- Docker 不可用：提示用户需自行安装 PostgreSQL 和 Redis
- Subagent 失败：报告错误，提示用户手动重试对应步骤
- shadcn CLI 失败：降级为手动写入 sonner.tsx（从模板）

## 附加资源

- 后端文件模板：[references/backend-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/backend-template.md)
- 前端文件模板：[references/frontend-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/frontend-template.md)
- Demo E2E 测试模板：[references/demo-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/demo-template.md)
- Unified Logger 包模板：[references/unified-logger-package-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/unified-logger-package-template.md)
- 脚本模板：[references/scripts-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/scripts-template.md)
- AGENTS.md 模板：[references/agents-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/agents-template.md)

## 相关引用

- `${CLAUDE_PLUGIN_ROOT}/skills/t-prd/SKILL.md` — 初始化完成后可开始 PRD 编写
- `${CLAUDE_PLUGIN_ROOT}/skills/t-design/SKILL.md` — 功能设计
- `${CLAUDE_PLUGIN_ROOT}/skills/t-task/SKILL.md` — 任务规划
