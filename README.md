# T-Tools

[English](README.en.md)

面向 Rust、React、Chrome 扩展、小程序与 Flutter 项目的 Claude Code plugin。它把 AI 编程拆成一套可执行、可恢复、可验收的工程工作流：

```text
Decision -> PRD / 技术预研（按主要未知项选择，可回环）-> 设计 -> 任务 -> 开发 -> 验收 -> Demo -> 发布
```

T-Tools 适合已经有产品文档、设计、任务拆解、开发、测试和 Demo 交付链路的项目。它的重点不是让模型自由发挥，而是用 skill 编排阶段、用 subagent 分工执行、用 protocol 固化共享契约，并在需要时用 check / accept 阶段收口质量。

推荐先读 [human/structure.md](human/structure.md)，理解 skill、subagent、protocol 如何协同；做需求前可用 [human/speech-template.md](human/speech-template.md) 先口述一遍真实意图。

本项目迭代的开发日志记录在 [linux.do](https://linux.do/t/topic/1988118/4)。

![T-Tools 工程工作流知识图谱](knowledge-graph.zh-CN.webp)

## 快速上手

不知道从哪个命令开始时，运行 `t-how`：它按你的目标讲解工作流并推荐入口命令。

前置条件：

- 已按 [安装](#安装) 加载插件
- 目标项目具备 `docs/` 和 `.ai/` 运行时目录
- 已配置 [`context7`](https://github.com/upstash/context7)

最短闭环：

```bash
# 产品立项判断，按主要未知项进入技术预研或 PRD
t-decision user-management

# 技术可行性、依赖或成本影响产品范围时先做预研；与 PRD 无固定顺序，进设计前收敛
t-tech-research user-management

# 生成 .ai/prd 与 .ai/user-stories 草稿
t-prd user-management

# 生成技术设计（主文档 + 分端设计）
t-design user-management

# 生成任务并按 phase 实现与测试；其他 phase 重复同样闭环
t-task user-management --phase backend
t-run user-management --phase backend

# GPT-5.6 Sol 级强模型的单主会话路径，合并规划与执行
t-super-run user-management --phase backend

# Web Demo/E2E 与最终验收（Flutter 对应 t-flutter-demo-run / t-flutter-demo-accept）
t-web-demo-run demo/e2e/<role>/<scenario>.e2e.ts
t-web-demo-accept <role>

# 实现和验收后发布正式 PRD / 用户故事
t-prd-publish user-management
```

`t-prd-check`、`t-design-check`、`t-task-check` 是可选质量检查，按风险选用。

## 阶段拆分

典型 Web 顺序是 `backend -> frontend -> web-demo`；典型 Flutter 顺序是 `backend -> flutter -> flutter-demo`。

- `backend`：后端接口、数据模型、权限、业务逻辑、后端测试和只读验收。
- `frontend`：React 页面、组件、状态、前端测试和只读验收。
- `extension`：WXT / Chrome MV3 入口、消息、存储、权限、Vitest 测试和只读验收；浏览器演示归 `web-demo`。
- `miniapp`：小程序页面、平台能力、构建验证和只读验收。
- `flutter`：Flutter View、Riverpod 状态、数据层、单元/widget/integration 测试和只读验收。
- `web-demo`：基于用户故事维护 Playwright Demo/E2E，并验收浏览器用户路径。
- `flutter-demo`：基于用户故事维护 Android Patrol 演示，覆盖真实 App 操作与原生系统 UI。

每个 phase 的闭环是 `t-task -> [t-task-check]（可选，按风险）-> t-run`，快速上手只以 backend 为例，其余 phase 重复同样闭环。`t-super-run` 是 GPT-5.6 Sol 级强模型的单主会话路径：合并规划与执行，`--phase` 必填，每次调用只执行一个 phase，完成后停止。miniapp 和 extension 不走 `t-super-run`，使用标准闭环。

扩展项目先准备 WXT 工程（`t-init` 尚不提供扩展模板），再运行 `t-design <feature>`、`t-task <feature> --phase extension`、`t-run <feature> --phase extension`。设计独立输出 `extension.md`；独立扩展 Demo 的 fixture 与 `--no-auto-env` 用法见 [扩展测试指南](guides/extension/testing.md)。

## 使用规则

- 所有 `t-*` 命令都需手工触发，模型不得自动调用。
- 不确定用哪个命令、想了解某阶段怎么跑时，运行 `t-how`：它按目标路由并讲解前置条件、产物和下一步。
- PRD、技术预研和设计需要人的明确校准：先按 [莫要偷懒](human/speech-template.md) 口述真实意图，交付时不得遗留未向用户确认的问题。

## 安装

```bash
# 1. 克隆本仓库
git clone <repo-url>

# 2. 在目标项目中启动 Claude Code 并加载插件
cd /your-project
claude --plugin-dir /path/to/skills
```

前置依赖：

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI 能正常使用
- MCP Server [`context7`](https://github.com/upstash/context7) 已配置
- 使用 Figma 工作流时，官方 [Figma MCP Server](https://developers.figma.com/docs/figma-mcp-server/) 已配置
- 使用 Figma 素材转换时，`ffmpeg` 与 `ffprobe` 已安装并可从 PATH 调用

使用 Codex、ZCode 等不支持 `claude --plugin-dir` 的工具时，见 [在其它 AI 编程工具中使用 t-tools](human/use-in-other-agents.md)：通过在 `~/.agents/skills/` 下放置路由 skill，把 `/t-tool <skill>` 指向克隆后的仓库目录。

## 使用本插件的项目

- [Herald](https://github.com/timzaak/herald) — 多租户认证与授权系统
- [RMQTT-Things](https://github.com/timzaak/rmqtt-things) — 基于 RMQTT 的物联网物模型管理平台
- [RWiki](https://github.com/timzaak/rwiki) — 基于 RAG 的知识库问答，单二进制、零外部数据库

> Java 后端支持见 `java` 分支。
