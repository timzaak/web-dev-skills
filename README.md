# T-Tools

[English](README.en.md)

面向 Rust、React、小程序与 Flutter 项目的 Claude Code plugin。它把 AI 编程拆成一套可执行、可恢复、可验收的工程工作流：

```text
Decision -> PRD / 技术预研（按主要未知项选择，可回环）-> 设计 -> 任务 -> 开发 -> 验收 -> Demo -> 发布
```

T-Tools 适合已经有产品文档、设计、任务拆解、开发、测试和 Demo 交付链路的项目。它的重点不是让模型自由发挥，而是用 skill 编排阶段、用 subagent 分工执行、用 protocol 固化共享契约，并在需要时用 check / accept 阶段收口质量。

推荐先读 [human/structure.md](human/structure.md)，理解 skill、subagent、protocol 如何协同；做需求前可用 [human/speech-template.md](human/speech-template.md) 先口述一遍真实意图。

本项目迭代的开发日志记录在 [linux.do](https://linux.do/t/topic/1988118/4)。

![T-Tools 工程工作流知识图谱](knowledge-graph.zh-CN.webp)

## 快速上手

不知道从哪个命令开始时，运行 `/t-tools:t-how`：它按你的目标讲解工作流并推荐入口命令。

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

# GPT-5.6 Sol 级强模型路径：由主会话规划、执行并用 Goal 持续到验收通过
# 此命令采用目标级 task，不生成供 t-task-check 检查的细粒度 item
/t-tools:t-super-run user-management --phase backend

# 运行 Web Demo/E2E 测试
/t-tools:t-web-demo-run demo/e2e/<role>/<scenario>.e2e.ts

# 串行运行全部非 live Demo/E2E，支持断点续跑
/t-tools:t-web-demo-run-all
# 批量 Demo 失败密集且疑似共享根因时：加 scan 参数先聚类再按唯一根因修
/t-tools:t-web-demo-run-all scan

# 运行 Android Flutter 用户故事演示
/t-tools:t-flutter-demo-run patrol_test/<domain>/<story>_test.dart --device <android-id>

# 串行运行全部 Patrol 演示，支持断点续跑
/t-tools:t-flutter-demo-run-all --device <android-id>

# Web / Flutter Demo 最终验收
/t-tools:t-web-demo-accept <role>
/t-tools:t-flutter-demo-accept <domain|all> --device <android-id>

# 实现和验收后发布正式 PRD / 用户故事
/t-tools:t-prd-publish user-management
```

`t-prd-check`、`t-design-check`、`t-task-check` 是可选质量检查：高风险需求、复杂设计、多人协作、长期维护或 AI 输出明显不稳定时建议运行；简单变更可直接进入下一阶段。`accept` 阶段仍是实现后的验收收口，不属于这三个可选检查。

## 阶段拆分

`t-task`、`t-task-check` 和 `t-run` 都按 phase 推进，其中 `t-task-check` 是可选检查。典型 Web 顺序是 `backend -> frontend -> web-demo`；典型 Flutter 顺序是 `backend -> flutter -> flutter-demo`。

- `backend`：后端接口、数据模型、权限、业务逻辑、后端测试和只读验收。
- `frontend`：React 页面、组件、状态、前端测试和只读验收。
- `miniapp`：小程序页面、平台能力、构建验证和只读验收。
- `flutter`：Flutter View、Riverpod 状态、数据层、单元/widget/integration 测试和只读验收。
- `web-demo`：基于用户故事维护 Playwright Demo/E2E，并验收浏览器用户路径。
- `flutter-demo`：基于用户故事维护 Android Patrol 演示，覆盖真实 App 操作与原生系统 UI。

每个 phase 都先运行 `/t-tools:t-task <feature> --phase <phase>`，随后可按风险选择运行 `/t-tools:t-task-check <feature> --phase <phase>`，再用 `/t-tools:t-run <feature> --phase <phase>` 串行执行 item。README 的快速上手只展开 backend 作为示例；其他 active phase 重复同样闭环。

`/t-tools:t-super-run <feature> --phase <backend|frontend|web-demo|flutter|flutter-demo>` 是针对 GPT-5.6 Sol（`gpt-5.6-sol`）及同等级强模型优化的单主会话执行路径：它合并任务规划与执行，dev/test 由主会话按 agent 规范直接执行，accept 派发对应只读 accept subagent 并把结论映射回状态，只按 backend/frontend/flutter 的 `dev -> test -> accept` 或 web-demo/flutter-demo 的 `dev -> accept` 记录目标级状态。`--phase` 必填，每次调用只执行指定的一个 phase，完成后停止并报告剩余未完成 phase，由用户再次调用启动。miniapp 使用 `t-task -> [t-task-check] -> t-run`。

## 关键使用规则

- 所有 `t-*` 命令都需手工触发（标准形式 `/t-tools:t-<skill>`），模型不得自动调用。
- `t-decision` 是产品立项门禁，先于 PRD 和技术预研，按主要未知项路由到 `t-prd` 或 `t-tech-research`。
- 任何阶段提问前先查 `.ai/decision-log/<feature>.md`，已确认或已裁决的决策不再重复询问。
- PRD、技术预研和设计交付时必须满足 `needs_user_answer=0`：影响范围、业务规则、权限、安全、显著成本或验收的问题先问用户，不得静默写成“待确认”、假设或风险。
- `t-prd` 与 `t-tech-research` 没有全局固定顺序，进入 `t-design` 前必须收敛且无未解释冲突；预研结论改变产品语义时重跑 `t-prd` 更新草稿。
- `t-prd` 只写 `.ai/prd` 与 `.ai/user-stories` 候选草稿，`t-prd-publish` 才把长期事实合并回 `docs/`。
- `t-design` 产出主文档与分端设计：后端设计先行并拥有 API 契约，前端与 Flutter 设计只消费契约。
- Figma 还原与动效精修是独立入口，不进入主链路：`t-figma-assets` 准备素材，`t-figma-impl` 整页还原，`t-figma-fix` 局部精修，`t-figma-ux` 动效精修。
- 辅助命令：`t-doc` 写项目文档；`t-dream` 跨阶段只读审计，PRD 治理写入需显式 `--govern-prd`；`t-simplify` 简化变更代码，不查正确性缺陷。推荐 `t-push` 前先跑 `/code-review --fix` 和 `t-simplify`，`t-push` 再清理注释、跑受影响 CI 并提交推送。

PRD、技术预研和设计需要人的明确校准：先按 [莫要偷懒](human/speech-template.md) 口述真实意图，AI 吞吐后先输出重点理解与待确认问题再生成产物；`t-prd` 后先口述你认可的 PRD 让 AI 对照修正，`t-design` 后从用户视角过一遍入口、路径、反馈、默认值和错误状态再让 AI 修正。

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
