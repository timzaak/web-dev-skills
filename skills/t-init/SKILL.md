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
- 仅允许英文、数字、连字符、下划线；拒绝 `..`、`/`、`\`；长度 1-50 字符

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
- 检查目标目录是否已存在同名目录；已存在且非空时询问用户是否覆盖
- 按各 references 模板和「输出文件清单」创建目录结构

### Step 2: 查询文档（主 Agent）

使用 Context7 查询关键依赖的最新文档，确保生成的代码使用当前最佳实践。必查依赖与关注点：

- **Axum** — 路由、状态共享、中间件、静态文件
- **Sea-ORM** — 数据库连接、实体定义、迁移
- **utoipa** — OpenApi derive、Swagger UI、Axum 集成
- **TanStack Router** — 文件路由、Vite 插件、createRouter
- **TanStack Query** — QueryClient、useQuery、Provider

如果某个 Context7 查询失败，降级到 `WebSearch` 搜索官方文档。如果都无法获取，基于已有知识生成但标注可能需要调整版本。将查询结果中的版本号和 API 用法保存，传递给后续 subagent。

### Step 3 ~ 5: 调度 subagent 生成代码（主 Agent）

按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 依次调度 subagent，prompt 使用 [references/subagent-prompts.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/subagent-prompts.md) 中的对应模板，替换全部占位符并附上 Step 2 收集的版本信息。模板中的关键约束已固化，不得省略：

| Step | subagent | 模板 | 输出目录 | 完成验证 |
|---|---|---|---|---|
| 3 | `t-tools:backend-dev` | backend-dev 模板 | `<project-name>/backend/` | `cargo check` |
| 4 | `t-tools:frontend-dev` | frontend-dev 模板 | `<project-name>/frontend/` | `npm install` + `type-check`（routeTree.gen.ts 错误除外） |
| 5 | `t-tools:web-demo-dev` | web-demo-dev 模板 | `<project-name>/demo/` | `npm install` + smoke test 全部通过 |

### Step 6: 生成项目本地 scripts（主 Agent）

将插件运行时脚本复制到目标项目根目录 `scripts/`，作为该项目后续环境启动、测试执行和 Demo 运行的优先入口。

复制来源：`${CLAUDE_PLUGIN_ROOT}/scripts/`

必须复制：
- `backend-test.py`
- `test-start.py`
- `test-stop.py`
- `demo-start.py`
- `demo-stop.py`
- `web-demo-test-runner.py`
- `web-demo-run-all.py`
- `debug-test.py`
- `cleanup-demo.py`
- `cleanup-test-logs.py`
- `web-demo-failure-summary.py`
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

收集各 subagent 的验证结果（见 Step 3 ~ 5 表格），并按「输出文件清单」用 Glob 确认所有文件都已创建。如果验证工具不可用，跳过并提示用户手动验证。

## 输出文件清单

完整清单见 [references/output-checklist.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/output-checklist.md)（Step 1 创建目录结构和 Step 8 验证时读取），覆盖四组必须产物：`backend/`（workspace 三 crate + 迁移与配置）、`frontend/`（Vite + TanStack 工程）、`scripts/` + `README.md` + `AGENTS.md`/`CLAUDE.md`、`demo/`（Playwright E2E 与冒烟测试）。

## 收尾输出

完成后在响应中明确说明：
- 项目路径、已生成的文件数量
- 各 subagent 验证结果（cargo check / npm install / smoke test）
- OpenAPI 开关位置（`config.toml` → `server.enable_openapi`）
- 项目本地脚本已生成到 `scripts/`，后续优先执行 `uv run scripts/<name>.py`；UnifiedLogger 通过 `npm install playwright-unified-logger` 安装
- Demo smoke test 运行命令（`cd demo && npx playwright test e2e/smoke.e2e.ts`）与日志环境变量说明（`UNIFIED_LOG_LEVEL` 等）
- AGENTS.md 和 CLAUDE.md 已生成，提醒用户填写项目描述
- 快速启动命令、需要用户手动完成的步骤（如复制 config、安装 Docker）
- 下一步建议（如 `/t-prd` 开始功能规划）

## 质量门禁

生成前逐项自检：
- 已查询 Context7 确认依赖版本，并把版本信息传递给了 subagent
- 后端 `cargo check`、前端 install + type-check、Demo smoke test 通过，或明确记录跳过原因
- sonner 等 UI 组件通过 CLI 命令生成（不是 AI 手写）；关键文件含中文注释，配置字段有完整说明
- demo smoke test 不依赖后端且能独立运行通过；demo 中 import 路径正确指向 `playwright-unified-logger`（npm 包）
- 所有占位符已替换为实际项目名称
- OpenAPI 开关、健康检查（DB + Redis）、启动自动迁移行为符合模板约束

## 失败处理

- 参数缺失或非法：终止并给出 `/t-init <project-name>` 示例
- 目标目录已存在且非空：询问是否覆盖
- Context7 查询失败：降级到 WebSearch，最终降级到已有知识
- cargo/npm 不可用：生成文件但跳过验证，提示用户手动检查
- Docker 不可用：提示用户需自行安装 PostgreSQL 和 Redis
- Subagent 失败：报告错误，提示用户手动重试对应步骤
- shadcn CLI 失败：降级为手动写入 sonner.tsx（从模板）

## 附加资源

- 输出文件清单：[references/output-checklist.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/output-checklist.md)
- Subagent prompt 模板：[references/subagent-prompts.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/subagent-prompts.md)
- 后端文件模板：[references/backend-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/backend-template.md)
- 前端文件模板：[references/frontend-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/frontend-template.md)
- Demo E2E 测试模板：[references/demo-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/demo-template.md)
- Unified Logger 包模板：[references/unified-logger-package-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/unified-logger-package-template.md)
- 脚本模板：[references/scripts-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/scripts-template.md)
- AGENTS.md 模板：[references/agents-template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/agents-template.md)
