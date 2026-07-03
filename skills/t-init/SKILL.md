---
name: t-init
description: Initialize a full-stack project skeleton with Java Spring Boot backend and React frontend (TypeScript + TanStack + Tailwind).
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

初始化一个全栈项目骨架：Java Spring Boot 后端 + React 前端 (TypeScript + TanStack + Tailwind) + Demo E2E。

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

- `{{PROJECT_NAME}}` — 项目名称（kebab-case，如 `my-project`）
- `{{PROJECT_NAME_PASCAL}}` — PascalCase（如 `MyProject`）
- `{{PROJECT_NAME_SNAKE}}` — snake_case（如 `my_project`）
- `{{PROJECT_PACKAGE}}` — Java package（默认 `com.example.<snake 去下划线>`）
- `{{PROJECT_PACKAGE_PATH}}` — package 路径（如 `com/example/myproject`）

## 生成流程

### Step 1: 验证参数（主 Agent）

- 校验 `$ARGUMENTS` 非空且合法
- 检查目标目录是否已存在同名目录
- 如果目录已存在且非空，询问用户是否覆盖
- 创建目录结构：

```text
<project-name>/
├── backend/
│   ├── pom.xml
│   └── src/
│       ├── main/
│       │   ├── java/{{PROJECT_PACKAGE_PATH}}/
│       │   │   ├── {{PROJECT_NAME_PASCAL}}Application.java
│       │   │   ├── config/
│       │   │   ├── health/
│       │   │   └── web/
│       │   └── resources/
│       └── test/java/{{PROJECT_PACKAGE_PATH}}/
├── frontend/
├── demo/
└── scripts/
```

### Step 2: 查询文档（主 Agent）

使用 Context7 查询关键依赖的最新文档，确保生成的代码使用当前最佳实践。

必查依赖：
- **Spring Boot**：project setup, actuator, testing, testcontainers
- **Spring Framework**：REST controller, validation, dependency injection, transaction
- **springdoc-openapi**：OpenAPI 3, Swagger UI, `/v3/api-docs`
- **TanStack Router**：前端文件路由
- **TanStack Query**：数据请求

如果某个 Context7 查询失败，降级到 `WebSearch` 搜索官方文档。如果都无法获取，基于已有知识生成但标注可能需要调整版本。

### Step 3: 生成后端（backend-dev subagent）

按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 使用 Agent 工具调度 `t-tools:backend-dev` subagent。后续 `frontend-dev` / `demo-dev` 调用同理。

Subagent prompt 必须要求：
- 读取后端模板文件 `${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/backend-template.md`
- 按模板生成 Spring Boot 后端文件并替换所有占位符
- 默认使用 Maven wrapper 和 Maven 项目结构
- 关键特性：
  - Spring Boot Web
  - Bean Validation
  - Actuator health
  - springdoc-openapi `/v3/api-docs` 与 Swagger UI
  - 统一错误响应入口
  - `GET /health` 兼容路由，可委托 Actuator/服务健康状态
- 完成后执行 `cd backend && mvn test`；无 wrapper 时执行 `mvn test`

### Step 4: 生成前端（frontend-dev subagent）

沿用 [references/frontend-template.md](references/frontend-template.md) 生成 React + TanStack 前端。`generate-api` 默认从 `../frontend/api.json` 生成客户端；后端 OpenAPI JSON 由 backend finalize 或脚本从 Spring Boot `/v3/api-docs` 导出。

必须通过 CLI 生成的 UI 组件仍由 CLI 生成，不手写覆盖。

### Step 5: 生成 Demo E2E 测试（demo-dev subagent）

沿用 [references/demo-template.md](references/demo-template.md)。默认后端基础 URL 为 `http://localhost:8080`，健康检查优先使用 `/actuator/health`，兼容 `/health`。

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
- 后端：`mvn test` 或 `mvn test` 是否通过
- 前端：`npm install` + `type-check` 是否通过（routeTree.gen.ts 错误除外）
- Demo：`npm install` + smoke test 是否通过
- 检查所有文件都已创建（Glob 验证）

如果验证工具不可用，跳过并提示用户手动验证。

## 输出文件清单

**后端（必须）：**
- [ ] `backend/pom.xml`
- [ ] `backend/src/main/java/{{PROJECT_PACKAGE_PATH}}/{{PROJECT_NAME_PASCAL}}Application.java`
- [ ] `backend/src/main/java/{{PROJECT_PACKAGE_PATH}}/web/HealthController.java`
- [ ] `backend/src/main/java/{{PROJECT_PACKAGE_PATH}}/health/HealthService.java`
- [ ] `backend/src/main/java/{{PROJECT_PACKAGE_PATH}}/web/ApiErrorHandler.java`
- [ ] `backend/src/main/resources/application.yml`
- [ ] `backend/src/test/java/{{PROJECT_PACKAGE_PATH}}/{{PROJECT_NAME_PASCAL}}ApplicationTests.java`

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
- [ ] `scripts/debug-test.py`
- [ ] `scripts/cleanup-demo.py`
- [ ] `scripts/cleanup-test-logs.py`
- [ ] `scripts/demo-failure-summary.py`
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
- 各 subagent 验证结果（Maven test / npm install / smoke test）
- OpenAPI 位置（`/v3/api-docs`，Swagger UI 由 springdoc 配置）
- 项目本地脚本已生成到 `scripts/`，后续优先执行 `uv run scripts/<name>.py`
- Demo smoke test 运行命令（`cd demo && npx playwright test e2e/smoke.e2e.ts`）
- AGENTS.md 和 CLAUDE.md 已生成，提醒用户填写项目描述
- 快速启动命令
- 需要用户手动完成的步骤（如复制配置、安装 Docker 等）
- 下一步建议（如 `/t-prd` 开始功能规划）

## 质量门禁

生成前逐项自检：
- 是否查询了 Context7 确认 Spring Boot、Spring Framework、springdoc 和前端依赖版本/用法
- 后端是否是 Java Spring Boot 项目结构
- 是否包含 Actuator health 与 `/health` 兼容入口
- 是否包含 `/v3/api-docs` OpenAPI 生成能力
- 后端是否能编译/测试通过（`mvn test` 或 `mvn test`）
- 前端组件是否通过 CLI 命令生成（不是 AI 手写）
- demo smoke test 是否不依赖后端且能独立运行通过
- 配置文件是否有完整注释说明关键字段
- 所有占位符是否已替换为实际项目名称

## 失败处理

- 参数缺失或非法：终止并给出 `/t-init <project-name>` 示例
- 目标目录已存在且非空：询问是否覆盖
- Context7 查询失败：降级到 WebSearch，最终降级到已有知识
- Maven/npm 不可用：生成文件但跳过验证，提示用户手动检查
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
