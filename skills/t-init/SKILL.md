---
name: t-init
argument-hint: <project-name>
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
  - Bash
  - WebSearch
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
---

# 项目初始化

初始化一个全栈项目骨架：Rust 后端 (Axum + Sea-ORM + Redis) + React 前端 (TypeScript + TanStack + Tailwind)。

## 适用范围

这是一个有副作用的脚手架生成 skill，会创建目录结构和写入大量文件。

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

## 先做什么

在生成代码之前，使用 Context7 查询关键依赖的最新文档，确保生成的代码使用当前最佳实践。

### 必查依赖（按顺序）

1. **Axum** — 路由、状态共享、中间件写法
   - `mcp__context7__resolve-library-id` → query: "axum web framework"
   - `mcp__context7__query-docs` → query: "router, state sharing, middleware, serve static files"

2. **Sea-ORM** — 数据库连接和实体定义
   - `mcp__context7__resolve-library-id` → query: "sea-orm rust database"
   - `mcp__context7__query-docs` → query: "database connection, entity generation, migration"

3. **utoipa** — OpenAPI 文档生成
   - `mcp__context7__resolve-library-id` → query: "utoipa rust openapi"
   - `mcp__context7__query-docs` → query: "OpenApi derive, swagger ui, axum integration"

4. **TanStack Router** — 前端文件路由
   - `mcp__context7__resolve-library-id` → query: "tanstack router react"
   - `mcp__context7__query-docs` → query: "file-based routing setup, vite plugin, createRouter"

5. **TanStack Query** — 数据请求
   - `mcp__context7__resolve-library-id` → query: "tanstack query react"
   - `mcp__context7__query-docs` → query: "QueryClient setup, useQuery, QueryClientProvider"

如果某个 Context7 查询失败，降级到 `WebSearch` 搜索官方文档。如果都无法获取，基于已有知识生成但标注可能需要调整版本。

## 项目结构

生成的项目结构如下：

```
<project-name>/
├── backend/
│   ├── Cargo.toml              # Workspace 根配置
│   ├── config.example.toml      # 配置模板
│   ├── migrations/              # SQLx 数据库迁移
│   │   └── 00001_init.sql
│   ├── domain-core/
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
│       │       └── sonner.tsx
│       ├── lib/
│       │   └── api-client.ts
│       └── routeTree.d.ts
├── packages/
│   └── playwright-unified-logger/
│       ├── package.json         # 独立 npm 包
│       ├── tsconfig.json
│       └── src/
│           ├── index.ts
│           ├── unified-logger.ts
│           ├── log-config.ts
│           ├── console-logger.ts
│           ├── network-logger.ts
│           ├── route-logger.ts
│           └── test-code-logger.ts
├── demo/
│   ├── package.json             # 依赖 unified-logger 包
│   ├── tsconfig.json
│   ├── playwright.config.ts
│   ├── eslint.config.js
│   ├── .gitignore
│   └── e2e/
│       ├── demo-basic.e2e.ts
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
│   └── dev-start.py
└── README.md
```

## 生成流程

### Step 1: 验证参数

- 校验 `$ARGUMENTS` 非空且合法
- 检查目标目录是否已存在同名目录
- 如果目录已存在且非空，询问用户是否覆盖

### Step 2: 查询文档

按"先做什么"部分的顺序查询 Context7，收集关键依赖的最新用法。
将查询到的版本信息用于后续文件生成。

### Step 3: 生成后端

读取 [references/backend-template.md](references/backend-template.md) 获取完整的后端文件模板。
模板中的占位符说明：

- `{{PROJECT_NAME}}` — 项目名称（kebab-case，如 `my-project`）
- `{{PROJECT_NAME_PASCAL}}` — PascalCase（如 `MyProject`）
- `{{PROJECT_NAME_SNAKE}}` — snake_case（如 `my_project`）

生成后端文件时：
1. 先创建目录结构
2. 按模板生成每个文件，替换占位符
3. 根据 Context7 查询结果调整依赖版本和 API 用法
4. 确保 OpenAPI 开关逻辑正确：`enable_openapi = true` 时暴露 `/swagger`，否则返回 404
5. 生成 `config.example.toml`，用户复制为 `config.toml` 后修改

后端关键特性：
- **OpenAPI 开关**：通过 `config.toml` 中的 `server.enable_openapi` 控制
- **健康检查**：`GET /health` 检查数据库和 Redis 连接
- **自动迁移**：启动时自动运行 SQLx 迁移
- **静态文件服务**：开发环境可代理前端，生产环境从 `static_dir` 提供前端文件

### Step 4: 生成前端

读取 [references/frontend-template.md](references/frontend-template.md) 获取完整的前端文件模板。

前端文件要求：
1. **代码注释**：每个关键文件都要有注释，解释：
   - 这个文件的用途
   - 使用的技术和为什么选择它
   - 如何修改/扩展
   - 相关的配置文件在哪里
2. 路由文件 (`__root.tsx`) 要有注释说明文件路由的工作方式
3. `main.tsx` 要有注释说明 React 应用启动流程
4. `vite.config.ts` 要有注释说明每个插件的作用
5. `package.json` 的 scripts 要有注释说明每个命令做什么

### Step 5: 生成 UnifiedLogger 包

读取 [references/unified-logger-package-template.md](references/unified-logger-package-template.md) 获取独立 npm 包的完整文件模板。

生成 `packages/playwright-unified-logger/` 目录，包含：
1. `package.json` — 包名为 `{{PROJECT_NAME}}-playwright-unified-logger`，peerDependency 为 `@playwright/test`
2. `tsconfig.json` — 输出到 `dist/`，declaration 生成
3. `src/index.ts` — 桶导出所有类和类型
4. `src/unified-logger.ts` — 统一日志协调器
5. `src/log-config.ts` — 环境变量配置（`UNIFIED_LOG_*` 前缀，兼容 `DEMO_LOG_*`）
6. `src/console-logger.ts` — 浏览器控制台日志捕获
7. `src/network-logger.ts` — API 请求/响应捕获（含脱敏）
8. `src/route-logger.ts` — SPA 路由变化追踪
9. `src/test-code-logger.ts` — Node.js 测试代码日志捕获

生成后执行 `npm install` 和 `npm run build` 验证包可编译。

### Step 6: 生成 Demo E2E 测试

读取 [references/demo-template.md](references/demo-template.md) 获取 demo 测试的完整文件模板。

生成 `demo/` 目录，包含：
1. `package.json` — 依赖 `{{PROJECT_NAME}}-playwright-unified-logger`（通过 `file:` 引用）
2. `tsconfig.json`
3. `playwright.config.ts` — 单 worker，headless Chrome
4. `eslint.config.js` — 禁止 `page.waitForTimeout()`
5. `.gitignore`
6. `e2e/fixtures/demo-auth.fixtures.ts` — demoLogger 和 authenticatedPage fixture
7. `e2e/fixtures/test-data.ts` — 测试数据管理
8. `e2e/helpers/auth.ts` — 登录/登出辅助函数
9. `e2e/helpers/environment-setup.ts` — 后端健康检查验证
10. `e2e/pages/base-page.ts` — Page Object 基类
11. `e2e/pages/login-page.ts` — 登录页 Page Object
12. `e2e/selectors.ts` — 集中式选择器定义
13. `e2e/demo-basic.e2e.ts` — 基础验证测试

生成后执行 `npm install` 验证依赖安装。

### Step 7: 生成脚本

读取 [references/scripts-template.md](references/scripts-template.md) 获取完整模板。

生成 `scripts/dev-start.py`：
- Docker 容器管理（PostgreSQL、Redis）
- 默认复用已有容器，`--clean` 参数重建
- 容器名称使用项目名称前缀避免冲突

### Step 8: 验证

生成完成后，执行以下验证：
1. 检查所有文件都已创建（Glob 验证）
2. 后端 `cargo check`（如果 cargo 可用）— 只做语法检查，不编译
3. 前端 `npm install` + `npm run type-check`（如果 npm 可用）
4. UnifiedLogger 包 `npm install && npm run build`（在 `packages/playwright-unified-logger/` 目录）
5. Demo `npm install`（在 `demo/` 目录）

如果验证工具不可用，跳过并提示用户手动验证。

## 输出文件清单

完成后确认以下文件存在：

**后端（必须）：**
- [ ] `backend/Cargo.toml`
- [ ] `backend/domain-core/Cargo.toml` + `src/lib.rs` + `src/config.rs` + `src/domain/health.rs` + `src/infrastructure/redis.rs`
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
- [ ] `frontend/src/components/ui/sonner.tsx`
- [ ] `frontend/src/lib/api-client.ts`

**脚本和文档：**
- [ ] `scripts/dev-start.py`
- [ ] `README.md`

**UnifiedLogger 包（必须）：**
- [ ] `packages/playwright-unified-logger/package.json`
- [ ] `packages/playwright-unified-logger/tsconfig.json`
- [ ] `packages/playwright-unified-logger/src/index.ts`
- [ ] `packages/playwright-unified-logger/src/unified-logger.ts`
- [ ] `packages/playwright-unified-logger/src/log-config.ts`
- [ ] `packages/playwright-unified-logger/src/console-logger.ts`
- [ ] `packages/playwright-unified-logger/src/network-logger.ts`
- [ ] `packages/playwright-unified-logger/src/route-logger.ts`
- [ ] `packages/playwright-unified-logger/src/test-code-logger.ts`

**Demo E2E 测试（必须）：**
- [ ] `demo/package.json`
- [ ] `demo/tsconfig.json`
- [ ] `demo/playwright.config.ts`
- [ ] `demo/eslint.config.js`
- [ ] `demo/.gitignore`
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
- OpenAPI 开关位置（`config.toml` → `server.enable_openapi`）
- UnifiedLogger 包位置和用法
- Demo 测试运行命令（`cd demo && npm test`）
- 日志环境变量说明（`UNIFIED_LOG_LEVEL` 等）
- 快速启动命令
- 需要用户手动完成的步骤（如复制 config、安装 Docker 等）
- 下一步建议（如 `/t-prd` 开始功能规划）

## 质量门禁

生成前逐项自检：
- 是否查询了 Context7 确认依赖版本和用法
- 后端 OpenAPI 开关逻辑是否正确（enable_openapi 控制路由注册）
- 后端是否能编译通过（`cargo check`）
- 前端代码是否有足够的中文注释
- 前端类型检查是否通过
- UnifiedLogger 包是否能编译通过（`npm run build`）
- demo 中 import 路径是否正确指向 `{{PROJECT_NAME}}-playwright-unified-logger`
- 配置文件是否有完整的注释说明每个字段
- 所有占位符是否已替换为实际项目名称

## 失败处理

- 参数缺失或非法：终止并给出 `/t-init <project-name>` 示例
- 目标目录已存在且非空：询问是否覆盖
- Context7 查询失败：降级到 WebSearch，最终降级到已有知识
- cargo/npm 不可用：生成文件但跳过验证，提示用户手动检查
- Docker 不可用：提示用户需自行安装 PostgreSQL 和 Redis

## 附加资源

- 后端文件模板：[references/backend-template.md](references/backend-template.md)
- 前端文件模板：[references/frontend-template.md](references/frontend-template.md)
- UnifiedLogger 包模板：[references/unified-logger-package-template.md](references/unified-logger-package-template.md)
- Demo E2E 测试模板：[references/demo-template.md](references/demo-template.md)
- 脚本模板：[references/scripts-template.md](references/scripts-template.md)

## 相关引用

- `skills/t-prd/SKILL.md` — 初始化完成后可开始 PRD 编写
- `skills/t-design/SKILL.md` — 功能设计
- `skills/t-task/SKILL.md` — 任务规划
