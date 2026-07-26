# T-Tools

[English](README.en.md)

面向 Rust、React、小程序与 Flutter 项目的 Claude Code plugin。它把 AI 编程拆成一套可执行、可恢复、可验收的工程工作流：

```text
Decision -> PRD / 技术预研（按主要未知项选择，可回环）-> 设计 -> 任务 -> 开发 -> 验收 -> Demo -> 发布
```

T-Tools 适合已经有产品文档、设计、任务拆解、开发、测试和 Demo 交付链路的项目。它的重点不是让模型自由发挥，而是用 skill 编排阶段、用 subagent 分工执行、用 protocol 固化共享契约，并在需要时用 check / accept 阶段收口质量。

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

# 技术可行性、依赖或成本会影响产品范围时，先做技术预研
/t-tools:t-tech-research user-management

# 产品边界已足以成稿时生成 .ai/prd 与 .ai/user-stories 草稿；
# 也可先生成草稿，再做技术预研，最后重跑本命令收敛草稿
/t-tools:t-prd user-management

# PRD 质量检查（可选，推荐高风险需求运行）
/t-tools:t-prd-check user-management

# 生成技术设计
/t-tools:t-design user-management

# 设计质量检查（可选，推荐复杂设计运行）
/t-tools:t-design-check user-management

# 生成 backend 阶段可执行任务
/t-tools:t-task user-management --phase backend

# 检查任务拆分、顺序和可执行性（可选，推荐复杂任务运行）
/t-tools:t-task-check user-management --phase backend

# 按阶段实现与测试
/t-tools:t-run user-management --phase backend

# 运行 Demo/E2E 测试
/t-tools:t-demo-run super-admin

# 最终验收
/t-tools:t-demo-accept super-admin

# 实现和验收后发布正式 PRD / 用户故事
/t-tools:t-prd-publish user-management
```

`t-prd-check`、`t-design-check`、`t-task-check` 是可选质量检查：高风险需求、复杂设计、多人协作、长期维护或 AI 输出明显不稳定时建议运行；简单变更可直接进入下一阶段。`accept` 阶段仍是实现后的验收收口，不属于这三个可选检查。

## 阶段拆分

`t-task`、`t-task-check` 和 `t-run` 都按 phase 推进，其中 `t-task-check` 是可选检查。典型 Web 顺序是 `backend -> frontend -> demo`；按实际交付端可插入 `miniapp` 和/或 `flutter`。

- `backend`：后端接口、数据模型、权限、业务逻辑、后端测试和只读验收。
- `frontend`：React 页面、组件、状态、前端测试和只读验收。
- `miniapp`：小程序页面、平台能力、构建验证和只读验收。
- `flutter`：Flutter View、Riverpod 状态、数据层、单元/widget/integration 测试和只读验收。
- `demo`：基于用户故事维护 Playwright Demo/E2E，并验收真实用户路径。

每个 phase 都先运行 `/t-tools:t-task <feature> --phase <phase>`，随后可按风险选择运行 `/t-tools:t-task-check <feature> --phase <phase>`，再用 `/t-tools:t-run <feature> --phase <phase>` 串行执行 item。README 的快速上手只展开 backend 作为示例；frontend、miniapp、flutter 和 demo 重复同样闭环。

## 关键使用规则

- 本 README 统一使用 `/t-tools:t-*` 作为标准调用形式。
- 所有 `t-*` skill 都是手工触发入口，不允许模型根据语义自动触发。
- `t-decision` 是 PRD 与技术预研前的产品立项门禁，输出 `.ai/decision/<feature>.md`；`Proceed` 根据主要未知项进入 `t-prd` 或 `t-tech-research`，`Research First` 先进入 `t-tech-research`。
- `t-prd` 与 `t-tech-research` 没有全局固定顺序：技术未知会改变范围时先预研，产品边界决定技术选择时先写 PRD 草稿；后续结论改变产品语义时必须重跑 `t-prd` 更新草稿，二者在进入 `t-design` 前必须收敛且不存在未解释冲突。
- `t-prd` 只写 `.ai/prd` 和 `.ai/user-stories` 候选需求；`t-prd-publish` 才把仍然成立的长期产品事实合并回 `docs/`。
- `t-doc` 用于项目文档、上手教程、API 参考、配置和部署说明，不用于 PRD、技术设计或零散文档修改。
- `t-dream` 默认只读审计 PRD、用户故事、设计/任务、实现事实与项目结构；需要写入 PRD 治理时显式使用 `--govern-prd`。
- `t-push` 会基于本次 diff 清理明显低价值注释、总结 commit message，并调用 `${CLAUDE_PLUGIN_ROOT}/scripts/push.py` 运行受影响 CI、提交和推送。
- 推荐 `t-push` 前先在 Claude Code 中运行 `/code-review --fix` 和 `/simplify`，让代码先经过独立审查与简化再收尾提交；二者与 `t-push` 的差异互相独立，不会相互覆盖。

PRD、技术预研和设计阶段需要人的明确校准。不会口播时，直接打开 [莫要偷懒](human/speech-template.md)，按里面的标题念：起步、用户故事梳理、UI/UX 梳理、第三方对接梳理、第三方库引入和结尾。AI 吞吐这段口播后，应先输出重点理解，评估可执行性、可行性和遗漏点，必要时联网查类似产品和最佳实践，再把内容与答案写入 `.ai/future/[feature].md`，并生成或修正 PRD、技术预研和设计输入。`/t-tools:t-prd` 后，先脱离生成物口述你认可的 PRD，再让 AI 对照修正。`/t-tools:t-design` 后，从用户视角明确 UX 入口、路径、反馈、默认值和错误状态，再让 AI 修正技术设计。

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
