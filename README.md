# T-Tools

[English](README.en.md)

面向 Rust + React 项目的 Claude Code plugin。它把 AI 编程拆成一条可执行、可恢复、可验收的工程工作流：

```text
Decision -> 技术预研 -> PRD -> 设计 -> 任务 -> 开发 -> 验收 -> Demo -> 发布
```

T-Tools 适合已经有产品文档、设计、任务拆解、开发、测试和 Demo 交付链路的项目。它的重点不是让模型自由发挥，而是用 skill 编排阶段、用 subagent 分工执行、用 protocol 固化共享契约、用 check / accept 阶段收口质量。

推荐先读 [human/structure.md](human/structure.md)，理解 skill、subagent、protocol 如何协同；做需求前可用 [human/speech-template.md](human/speech-template.md) 先口述一遍真实意图。

![T-Tools 知识图谱](knowledge-graph.png)

## 快速上手

前置条件：

- 已按 [安装](#安装) 加载插件
- 目标项目具备 `docs/` 和 `.ai/` 运行时目录
- 已配置 [`context7`](https://github.com/upstash/context7)

最短闭环：

```bash
# 产品立项判断
/t-tools:t-decision user-management

# 需要可行性、依赖或成本判断时使用
/t-tools:t-tech-research user-management

# 生成 .ai/prd 与 .ai/user-stories 草稿和 HTML Preview
/t-tools:t-prd user-management

# PRD 质量门禁
/t-tools:t-prd-check user-management

# 生成技术设计
/t-tools:t-design user-management

# 设计质量门禁
/t-tools:t-design-check user-management

# 生成 backend 阶段可执行任务
/t-tools:t-task user-management --phase backend

# 检查任务拆分、依赖和可执行性
/t-tools:t-task-check user-management --phase backend

# 按阶段实现与测试
/t-tools:t-run user-management --phase backend

# 本地 diff 审查
/t-tools:t-code-review

# 运行 Demo/E2E 测试
/t-tools:t-demo-run super-admin

# 最终验收
/t-tools:t-demo-accept super-admin

# 实现和验收后发布正式 PRD / 用户故事
/t-tools:t-prd-publish user-management
```

只记住一条规则：不要跳过 check / accept。这个插件的价值不只是生成内容，而是在每个阶段把问题拦住，避免错误继续流向下游。

## 阶段拆分

`t-task`、`t-task-check` 和 `t-run` 都按 phase 推进。典型顺序是 `backend -> frontend -> demo`，启用小程序时可插入 `miniapp`。

- `backend`：后端接口、数据模型、权限、业务逻辑、后端测试和只读验收。
- `frontend`：React 页面、组件、状态、前端测试和只读验收，依赖 backend 完成。
- `demo`：基于用户故事维护 Playwright Demo/E2E，并验收真实用户路径，依赖前置交付阶段完成。

每个 phase 都先运行 `/t-tools:t-task <feature> --phase <phase>`，再运行 `/t-tools:t-task-check <feature> --phase <phase>`，通过后用 `/t-tools:t-run <feature> --phase <phase>` 串行执行 item。README 的快速上手只展开 backend 作为第一阶段示例；backend 完成后，对 frontend 和 demo 重复同样闭环。

## 关键使用规则

- 本 README 统一使用 `/t-tools:t-*` 作为标准调用形式。
- 所有 `t-*` skill 都是手工触发入口，不允许模型根据语义自动触发。
- `t-decision` 是 PRD 前的产品立项门禁，输出 `.ai/decision/<feature>.md` 和 `.ai/preview/decision/<feature>.html`；结论为 `Proceed` 或 `Research First` 后再进入后续流程。
- `t-prd` 只写 `.ai/prd` 和 `.ai/user-stories` 候选需求；`t-prd-publish` 才把仍然成立的长期产品事实合并回 `docs/`。
- `t-doc` 用于项目文档、上手教程、API 参考、配置和部署说明，不用于 PRD、技术设计或零散文档修改。
- `t-dream` 默认只读审计 PRD、用户故事、设计/任务、实现事实与项目结构；需要写入 PRD 治理时显式使用 `--govern-prd`。
- `t-code-review` 默认审查当前分支和工作区改动，只输出高置信 correctness bug 与明确适用的规则违反；传 `--comment` 时才尝试评论 GitHub PR。
- `t-push` 会基于本次 diff 清理明显低价值注释、总结 commit message，并调用 `${CLAUDE_PLUGIN_ROOT}/scripts/push.py` 运行受影响 CI、提交和推送。

PRD、技术预研和设计阶段需要人的明确校准。不会口播时，直接打开 [莫要偷懒](human/speech-template.md)，按里面的标题念：起步、用户故事梳理、UI/UX 梳理、第三方对接梳理、第三方库引入和结尾。AI 吞吐这段口播后，应先输出重点理解，评估可执行性、可行性和遗漏点，必要时联网查类似产品和最佳实践，再把内容与答案写入 `.ai/future/[feature].md`，并生成或修正 PRD、技术预研和设计输入。`/t-tools:t-prd` 后，先脱离生成物口述你认可的 PRD，再看 HTML Preview 并让 AI 对照修正。`/t-tools:t-design` 后，从用户视角明确 UX 入口、路径、反馈、默认值和错误状态，再让 AI 修正技术设计。

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

使用 Codex、ZCode 等不支持 `claude --plugin-dir` 的工具时，见 [在其它 AI 编程工具中使用 t-tools](human/use-in-other-agents.md)：通过在 `~/.agents/skills/` 下放置路由 skill，把 `/t-tool <skill>` 指向克隆后的仓库目录。

## 使用本插件的项目

- [Herald](https://github.com/timzaak/herald) — 多租户认证与授权系统
- [RMQTT-Things](https://github.com/timzaak/rmqtt-things) — 基于 RMQTT 的物联网物模型管理平台
- [RWiki](https://github.com/timzaak/rwiki) — 基于 Wiki.js 数据的 AI 增强知识库

> Java 后端支持见 `java` 分支。
