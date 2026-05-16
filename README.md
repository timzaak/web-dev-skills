# T-Tools

[English](README.en.md)

面向 Rust + React 项目的 Claude Code plugin。它把 `PRD -> 设计 -> 任务 -> 开发 -> 验收 -> Demo` 串成一套可复用工作流，让你不用反复设计 prompt、切换上下文或手工维护阶段边界。

适合这类团队和项目：

- 已经有明确的产品文档、设计、任务拆解、开发、测试、Demo 交付链路
- 希望把 Claude Code 从“临时问答”升级成“可执行的工程工作流”
- 需要 sub-agent 分工、阶段门禁、标准化产物，而不是一次性自由发挥

## 为什么用它

- 上手快：直接按 `/t-tools:t-*` 命令顺序推进，不需要自己设计整套提示词和协作流程
- 交付稳：关键阶段自带检查和验收命令，减少文档跑偏、任务漏拆、Demo 不可执行
- 协作清：skill、agent、guide、protocol 已分层，适合多人或长期项目持续复用

## 完整工作流

```text
/t-tools:t-init <project-name> (可选，初始化全栈项目骨架)
  /t-tools:t-tech-research (可选，评估需求技术可行性)
  /t-tools:t-prd
  -> /t-tools:t-prd-check
  -> /t-tools:t-design
  -> /t-tools:t-design-check
  -> /t-tools:t-task
  -> /t-tools:t-task-check
  -> /t-tools:t-run
  -> /t-tools:t-backend-finalize
  -> /t-tools:t-demo-run
  -> /t-tools:t-demo-accept
  -> /t-tools:t-release [版本号]
```

其中：

- `/t-tools:t-prd-check` 是 PRD 与 user story 质量门禁，不是可有可无的补充命令
- `/t-tools:t-demo-accept` 是 Demo 阶段验收门禁，用来确认测试覆盖、可运行性和交付质量

常见辅助命令：

- `/t-tools:t-init <project-name>`：初始化全栈项目骨架（Rust Axum + React TanStack），生成后端、前端、E2E 测试、开发脚本等完整目录结构
- `/t-tools:t-tech-research`：在写 PRD 之前评估需求的技术可行性，包括依赖缺口分析、库调研、影响分析和可行性判定
- `/t-tools:t-doc <project-or-module-name>`：扫描目标项目代码库，生成面向新人的教程文档，默认写入 `docs/tutorials/<name>/`
- `/t-tools:t-consistency-check`：复核后端 PRD 与实现是否一致，不承担全域 DDD 总检查
- `/t-tools:t-demo-run-all`：批量执行 Demo 测试
- `/t-tools:t-release [版本号]`：版本发布，更新项目版本号、创建 git commit 和 tag、推送到远程。版本号遵循语义化版本（如 `0.2.0`），最终 tag 一律不带 `v` 前缀；留空则基于最新 semver tag 推荐，并自动去掉历史 tag 中的 `v` 前缀。仅在 `main` 分支且工作区干净时执行，自动更新 `backend/Cargo.toml`、`frontend/package.json`、`demo/package.json`，编译验证通过后提交并推送

## 安装

```bash
# 1. 克隆本仓库
git clone <repo-url>

# 2. 在目标项目中启动 Claude Code 并加载插件
cd /your-project
claude --plugin-dir /path/to/skills
```

前置依赖：

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI 已安装并登录
- MCP Server `context7` 已配置（用于查询第三方库文档）

## 3 分钟快速上手

前置条件：

- 已按上方 [安装](#安装) 步骤加载 t-tools 插件
- 目标项目具备运行时目录：`docs/`、`.ai/`
- 已启用 `context7`

最短闭环示例：

```bash
/t-tools:t-prd user-management
/t-tools:t-prd-check user-management
/t-tools:t-design user-management
/t-tools:t-task user-management
/t-tools:t-run user-management --phase backend
/t-tools:t-demo-run super-admin
/t-tools:t-demo-accept super-admin
```

执行顺序可以这样理解：

- `/t-tools:t-prd user-management`：若 PRD 不存在则创建，已存在则基于现有内容补齐或更新相关 PRD 与 user story
- `/t-tools:t-prd-check user-management`：马上做产品文档质量门禁，避免把问题带入设计阶段
- `/t-tools:t-design user-management`：基于 PRD 产出技术设计
- `/t-tools:t-task user-management`：把设计转换成可执行任务
- `/t-tools:t-run user-management --phase backend`：按阶段驱动实现与测试
- `/t-tools:t-demo-run super-admin`：运行该角色的 Demo/E2E 测试
- `/t-tools:t-demo-accept super-admin`：做最终验收，确认故事映射、编译、执行和质量要求都通过

如果你只想记住一件事：不要跳过 check / accept 阶段。这个 plugin 的价值不只是“帮你生成内容”，而是“帮你在每个阶段收口”。

补充说明：

- 本 README 统一使用 `/t-tools:t-*` 作为标准调用形式
- `t-doc` 用于项目文档、上手教程、API 参考、配置和部署说明，不用于 PRD、技术设计或只改某个文档片段
- `t-consistency-check` 是后端专项一致性检查，不等价于旧仓库中的全域 DDD 检查
- `t-backend-test-run` 是内部执行型 skill，供 `backend-test` 等流程复用，不作为推荐的手动入口

## 常用入口

- 设计思路导读：[human/structure.md](/human/structure.md)（推荐先读，理解 skill、subagent、protocol 如何协同驱动 AI 编程）
- 产品规范入口：[guides/product/index.md](/guides/product/index.md)
- 后端开发与门禁：[guides/backend/index.md](/guides/backend/index.md)
- 前端开发与门禁：[guides/frontend/index.md](/guides/frontend/index.md)
- 小程序开发与门禁：[guides/miniapp/index.md](/guides/miniapp/index.md)
- Demo 测试与诊断：[guides/demo/index.md](/guides/demo/index.md)
- 跨领域总纲：[guides/core/index.md](/guides/core/index.md)
- 协议索引：[protocols/index.md](/protocols/index.md)

## 仓库边界

这是 plugin 源码仓库，不是目标业务仓库。

- 插件资源主要在 `skills/`、`agents/`、`guides/`、`protocols/`、`scripts/`
- 插件清单位于 `.claude-plugin/plugin.json`
- 目标项目运行时主要依赖 `docs/`、`.ai/`

引用插件内部文件时统一使用 `${CLAUDE_PLUGIN_ROOT}` 语义路径。根级 `README.md` 只负责说明优势、工作流和快速上手；更细的规则请进入对应 guide / protocol。

## 使用本插件的项目

- [herald](https://github.com/timzaak/herald) — 多租户认证与授权系统（Rust Axum + SeaORM + PostgreSQL / React 19 + TanStack），支持单租户与多租户场景的认证服务
- [rmqtt-things](https://github.com/timzaak/rmqtt-things) — 基于 RMQTT 的物联网物模型管理平台（Rust Axum + SQLx + PostgreSQL / React 19 + TanStack），支持设备管理、命令下发、OTA 升级与 TLS 证书签发

## 依赖

- `Context7`：供 `backend-dev`、`backend-test`、`frontend-dev`、`frontend-test` 查询第三方库文档
- `/simplify`：可选，用于 `t-backend-finalize` 收口审查
