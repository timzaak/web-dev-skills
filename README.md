# T-Tools

[English](README.en.md)

T-Tools 是面向 Rust、React、Chrome 扩展、小程序、Flutter 与 Shopify 项目的 Claude Code plugin。它把 AI 编程从“模型自由发挥”约束成**可执行、可恢复、可验收**的工程工作流：

```text
Decision -> PRD / 技术预研（按主要未知项选择，可回环）-> 设计 -> 开发 -> 验收 -> Demo -> 发布
```

![T-Tools 工程工作流知识图谱](knowledge-graph.zh-CN.webp)

## 为什么是 T-Tools

- **一条命令一个阶段。** 立项、需求、设计、实现、验收、Demo、发布各有明确入口，产物落盘、状态可查。
- **中断可恢复。** 任何阶段被打断，重跑同一命令即从断点继续，不依赖会话记忆。
- **独立验收，证据说话。** accept 由只读 subagent 按[公共验收协议](protocols/acceptance-contract.md)出结论：必要门禁必须通过，未解决的 P0/P1 阻断交付。
- **人裁决，AI 执行。** 产品取舍由人确认——`t-prd` 写入前主动澄清缺少依据的选择；AI 负责执行、测试和证据。
- **多端覆盖。** Web、Chrome 扩展、小程序、Flutter、Shopify 与 Figma 还原各有专用阶段和演示验收。

想理解 skill、subagent、protocol 如何协同，读 [human/structure.md](human/structure.md)。

## 安装

```bash
git clone <repo-url>
cd /your-project
claude --plugin-dir /path/to/skills
```

前置条件：

- MCP Server [`context7`](https://github.com/upstash/context7) 已配置
- 按需配置：Chrome DevTools MCP（`--autoConnect`，扩展真实浏览器协作，见[用户 Chrome 调试指南](guides/extension/live-browser.md)）；官方 [Figma MCP Server](https://developers.figma.com/docs/figma-mcp-server/)（Figma 工作流，素材转换另依赖 Python `Pillow`、`ffmpeg`/`ffprobe`、`svgo` 和 [kyz](https://github.com/byteowlz/kyz) 凭据代理）
- 使用 Codex、ZCode 等不支持 `claude --plugin-dir` 的工具时，见[在其它 AI 编程工具中使用 t-tools](human/use-in-other-agents.md)

`.ai/` 与 `docs/` 运行时目录无需预先创建，工作流执行过程中会自行创建；Web 与扩展 Demo 的日志库 [`playwright-unified-logger`](https://github.com/timzaak/playwright-unified-logger) 由 `t-init` 自动安装。

## 快速上手

不知道从哪个命令开始时，运行 `t-how`：它按你的目标讲解工作流并推荐入口命令。最短闭环：

```bash
t-decision user-management      # 立项：按主要未知项进入 PRD 或技术预研
t-prd user-management           # PRD 草稿（.ai/prd），主动澄清关键产品选择
t-design user-management        # 技术设计：主文档 + 分端设计
t-super-run user-management --phase backend   # 实现 + 测试 + 独立验收
t-super-run user-management --phase frontend  # 逐 phase 推进；中断后重跑同一命令恢复
t-web-demo-run demo/e2e/<role>/<scenario>.e2e.ts   # 用户故事 Demo/E2E
t-web-demo-accept <role>                           # 浏览器用户路径验收
t-prd-publish user-management   # 验收通过后发布正式 PRD / 用户故事
```

阶段顺序：Web 为 `backend -> frontend -> web-demo`，扩展为 `extension -> extension-demo`，Flutter 为 `backend -> flutter -> flutter-demo`，Shopify 为 `shopify-app -> shopify-extension -> web-demo`。全部阶段与启用条件见[阶段执行协议](protocols/task-phase-execution.md#phases)。

`t-prd-check`、`t-design-check`、`t-task-check` 是可选质量检查，按风险选用；需要单独审阅任务计划或细粒度分工时，用 `t-task -> t-run` 代替 `t-super-run`。

## 能力一览

| 你要做的事 | 入口 |
| --- | --- |
| 产品立项、PRD、技术预研 | `t-decision` / `t-prd` / `t-tech-research`，收口用 `t-prd-publish` |
| 设计、实现与验收 | `t-design`，然后 `t-super-run <feature> --phase <phase>` |
| 用户故事 Demo 与验收 | `t-web-demo-*` / `t-extension-demo-*` / `t-flutter-demo-*` 及对应 `*-accept` |
| Chrome 扩展项目 | 先按[扩展初始化指南](guides/extension/initialization.md)建 WXT 工程，再 `--phase extension`；真实加载演示用 `t-init --extension-demo` |
| Shopify App 项目 | `t-init --shopify <project-name>` 建工程，规范见 [Shopify 开发指南](guides/shopify/development.md)；`shopify app deploy` 在 `t-push` 后由用户手动执行 |
| Figma 还原 | `t-figma-assets` -> `t-figma-impl`：人类设计稿完成约 30% 即可介入编码，人确认范围、AI 分块实现并交付验收，见[素材处理指南](guides/figma/assets.md) |
| 提交与质量收口 | `t-review`（只报告正确性缺陷）-> `t-simplify`（四角度清理）-> `t-push`（[push 执行协议](protocols/push-execution-contract.md)）；review / simplify 不能替代 accept |
| 新项目脚手架 | `t-init <project-name>`（Rust + React 全栈骨架；Shopify 用 `--shopify`） |
| 维护插件与项目知识 | `t-skill`（创建/修改 skill）、`t-doc`（教程文档）、`t-dream`（上下文审计）、`t-release`（发版） |

每个命令的参数、前置条件和下一步，运行 `t-how` 交互式讲解。

## 使用规则

- 所有 `t-*` 命令都需手工触发，模型不得自动调用。
- PRD、技术预研和设计需要人的明确校准：先按[莫要偷懒](human/speech-template.md)口述真实意图，交付时不得遗留未向用户确认的问题。

## 使用本插件的项目

- [Herald](https://github.com/timzaak/herald) — 多租户认证与授权系统
- [RMQTT-Things](https://github.com/timzaak/rmqtt-things) — 基于 RMQTT 的物联网物模型管理平台
- [RWiki](https://github.com/timzaak/rwiki) — 基于 RAG 的知识库问答，单二进制、零外部数据库
- [OnceWise](https://github.com/timzaak/OnceWise) — 智能表单自动化助手，一键告别重复填写

> Java 后端支持见 `java` 分支。
>
> `general` 分支是[泛化方案](human/generalization.md)的落地：移除生产技术栈预设，改用通用 project 角色适配任意技术栈，移出的领域资产转为可选导出模板。

## 了解更多

- [human/structure.md](human/structure.md) — skill、subagent、protocol 如何协同
- [protocols/](protocols/) — 阶段执行、验收、push 等共享契约
- [guides/](guides/) — 后端、前端、扩展、Shopify、Figma 等领域工程规范
- 开发迭代日志：[linux.do](https://linux.do/t/topic/1988118/4)
