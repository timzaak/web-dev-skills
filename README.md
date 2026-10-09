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

按 [安装](#安装) 加载插件并满足前置条件后，最短闭环：

```bash
# 产品立项判断，按主要未知项进入技术预研或 PRD
t-decision user-management

# 技术可行性、依赖或成本影响产品范围时先做预研；与 PRD 无固定顺序，进设计前收敛
t-tech-research user-management

# 优先读取同一 feature 的 Decision Brief 和技术预研；已有相关 PRD 必须查阅
# 生成 .ai/prd 与 .ai/user-stories 草稿
t-prd user-management

# 可按风险运行 t-prd-check，或直接进入设计
# 生成技术设计（主文档 + 分端设计）
t-design user-management

# 合并任务规划、实现与测试，按 phase 执行；其他 phase 重复同样闭环
t-super-run user-management --phase backend

# Web Demo/E2E 与最终验收（扩展、Flutter 有独立入口）
t-web-demo-run demo/e2e/<role>/<scenario>.e2e.ts
t-web-demo-accept <role>
# Chrome 扩展真实加载演示与验收
t-extension-demo-run demo/e2e/extension/<scenario>.e2e.ts
t-extension-demo-run-all
t-extension-demo-accept all

# 实现和验收后发布正式 PRD / 用户故事
t-prd-publish user-management
```

`t-prd-check`、`t-design-check`、`t-task-check` 是可选质量检查，按风险选用。

## 阶段拆分

典型 Web 顺序是 `backend -> frontend -> web-demo`；典型扩展顺序是 `extension -> extension-demo`（有后端改动时前置 backend）；典型 Flutter 顺序是 `backend -> flutter -> flutter-demo`。

- `backend`：后端接口、数据模型、权限、业务逻辑、后端测试和只读验收。
- `frontend`：React 页面、组件、状态、前端测试和只读验收。
- `extension`：WXT / Chrome MV3 入口、消息、存储、权限、Vitest 测试和只读验收。
- `miniapp`：小程序页面、平台能力、构建验证和只读验收。
- `flutter`：Flutter View、Riverpod 状态、数据层、单元/widget/integration 测试和只读验收。
- `web-demo`：基于用户故事维护 Playwright Demo/E2E，并验收浏览器用户路径。
- `extension-demo`：基于用户故事维护真实加载扩展的 Playwright 集成演示，验收跨上下文用户路径、权限和生命周期。
- `flutter-demo`：基于用户故事维护 Android Patrol 演示，覆盖真实 App 操作与原生系统 UI。

每个 phase 的默认闭环是 `t-super-run`：主会话按当前角色规范持续完成实现、测试和修复，accept 派发对应只读 subagent 独立验收。`--phase` 必填，每次只执行一个 phase，完成后停止，中断后用同一命令恢复。需要单独审阅任务计划或细粒度 item 分工时，改用 `t-task -> t-run` 标准链路，两套状态互相独立。

review、simplify 或 CI 修复使证据失效时，先补跑必要回归和独立验收再提交；push 门禁与中断恢复见 [push 执行协议](protocols/push-execution-contract.md)。

扩展项目按 [扩展初始化指南](guides/extension/initialization.md) 准备 WXT 工程；需要真实加载扩展的集成演示基础设施时，在目标项目运行 `t-init --extension-demo`。演示 fixture、环境与验收见 [扩展演示指南](guides/extension/demo-testing.md)。

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

前置条件：

- MCP Server [`context7`](https://github.com/upstash/context7) 已配置
- 扩展开发涉及用户当前 Chrome 现场（标签页、登录态、已安装扩展）时，Chrome DevTools MCP（`--autoConnect`）已按 [用户 Chrome 调试指南](guides/extension/live-browser.md) 配置
- 使用 Figma 工作流时，官方 [Figma MCP Server](https://developers.figma.com/docs/figma-mcp-server/) 与 Chrome DevTools MCP 已配置；素材转换依赖 `ffmpeg`/`ffprobe`、`svgo` 和 [kyz](https://github.com/byteowlz/kyz) 凭据代理

`.ai/` 与 `docs/` 运行时目录无需预先创建，工作流执行过程中会自行创建。

使用 Codex、ZCode 等不支持 `claude --plugin-dir` 的工具时，见 [在其它 AI 编程工具中使用 t-tools](human/use-in-other-agents.md)：通过在 `~/.agents/skills/` 下放置路由 skill，把 `/t-tool <skill>` 指向克隆后的仓库目录。

## 使用本插件的项目

- [Herald](https://github.com/timzaak/herald) — 多租户认证与授权系统
- [RMQTT-Things](https://github.com/timzaak/rmqtt-things) — 基于 RMQTT 的物联网物模型管理平台
- [RWiki](https://github.com/timzaak/rwiki) — 基于 RAG 的知识库问答，单二进制、零外部数据库
- [OnceWise](https://github.com/timzaak/OnceWise) — 智能表单自动化助手，一键告别重复填写

> Java 后端支持见 `java` 分支。
