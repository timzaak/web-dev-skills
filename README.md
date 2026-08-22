# T-Tools

[English](README.en.md)

面向 Java Spring Boot、React、小程序与 Flutter 项目的 Claude Code plugin。它把 AI 编程拆成一套可执行、可恢复、可验收的工程工作流：

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

`/t-tools:t-super-run <feature> [--phase backend|frontend|web-demo|flutter|flutter-demo]` 是针对 GPT-5.6 Sol（`gpt-5.6-sol`）及同等级强模型优化的单主会话执行路径：它合并任务规划与执行，不调用 subagent，只按 backend/frontend/flutter 的 `dev -> test -> accept` 或 web-demo/flutter-demo 的 `dev -> accept` 记录目标级状态。miniapp 使用 `t-task -> [t-task-check] -> t-run`。

## 关键使用规则

- 本 README 统一使用 `/t-tools:t-*` 作为标准调用形式。
- 所有 `t-*` skill 都是手工触发入口，不允许模型根据语义自动触发。
- `t-super-run` 读取既有 agent 规范作为当前角色指南，但不启动 subagent；启动和恢复前必须通过完整设计状态与结构校验，读取对应分端设计，并用设计指纹识别变更后重新规划受影响 task。
- `t-decision` 是 PRD 与技术预研前的产品立项门禁，输出 `.ai/decision/<feature>.md`；`Proceed` 根据主要未知项进入 `t-prd` 或 `t-tech-research`，`Research First` 先进入 `t-tech-research`。
- 已确认决策、已解决问题和显式延期问题跨阶段写入 `.ai/decision-log/<feature>.md`，使用稳定 DEC/Q ID；任何阶段提问前必须先查账本，避免重复询问或采用已被替代的决定。
- PRD、技术预研和设计交付时必须满足 `needs_user_answer=0`。影响范围、业务规则、权限、安全、兼容性、显著成本、验收或风险接受的问题必须先询问用户，不得静默写成“待确认”、假设或风险后继续。
- `t-prd` 与 `t-tech-research` 没有全局固定顺序：技术未知会改变范围时先预研，产品边界决定技术选择时先写 PRD 草稿；后续结论改变产品语义时必须重跑 `t-prd` 更新草稿，二者在进入 `t-design` 前必须收敛且不存在未解释冲突。
- `t-prd` 只写 `.ai/prd` 和 `.ai/user-stories` 候选需求；`t-prd-publish` 才把仍然成立的长期产品事实合并回 `docs/`。
- `t-design` 产出"主文档 + 分端设计"：主文档 `.ai/design/<feature>.md` 承载目标范围、跨端契约摘要、测试与风险汇总和全量文件影响范围；后端、前端、Flutter 各自的深入设计在 `.ai/design/<feature>/` 下由对应设计 agent 生成。后端设计先行并拥有 API 契约单一来源，前端与 Flutter 设计只消费契约不重新定义。
- `t-doc` 用于项目文档、上手教程、API 参考、配置和部署说明，不用于 PRD、技术设计或零散文档修改。
- `t-dream` 默认只读审计 PRD、用户故事、设计/任务、实现事实与项目结构；需要写入 PRD 治理时显式使用 `--govern-prd`。
- `t-figma <figma-url> <target-file>` 把 Figma 设计还原进已有前端文件并用 getComputedStyle 测量法评估还原度（spec 提取一次固化，已有代码 token/动效/组件强制复用，delta 驱动迭代收敛）。它是独立触发入口，不进入 Decision→Release 主链路；需要 Figma MCP。资产默认保存 Figma 返回的原始字节并沿用项目目录约定，项目级 `DESIGN.md` 若存在则优先。
- `t-push` 会基于本次 diff 清理明显低价值注释、总结 commit message，并调用 `${CLAUDE_PLUGIN_ROOT}/scripts/push.py` 运行受影响 CI、提交和推送。
- `t-simplify` 对变更代码（默认为上游区间加未提交变更，也可指定 PR / 分支 / 文件目标）做复用、简化、效率、抽象层级四个角度的并行只读审查，去重后直接应用修复；只做质量清理，不找正确性缺陷（那属于 `/code-review` 和各阶段 accept）。Agent tool 不可用时降级为主会话单遍审查并在报告中如实声明。
- 推荐 `t-push` 前先在 Claude Code 中运行 `/code-review --fix` 和 `/t-tools:t-simplify`，让代码先经过独立审查与简化再收尾提交；它们与 `t-push` 的注释清理互相独立，不会相互覆盖。

### `t-simplify` 来源说明

`t-simplify` 复刻自 Claude Code 内置 `/simplify` 命令的提示词：主流程与 inline 降级来自 [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)（MIT）对 v2.1.154 slash command 与 v2.1.213 inline 模式的二进制提取。v2.1.154 中四个审查角度的指引还是运行时注入变量、未随提取发布，本插件最初按公开行为还原；v2.1.232 已把它们内嵌进二进制，本插件随即按本机二进制提取逐字校准了四个角度、Phase 0 变更收集（上游区间 + 未提交变更）和 `<target>` 参数语义，落在 [`protocols/simplify-cleanup-contract.md`](protocols/simplify-cleanup-contract.md)；并按本插件约定补充了 `simplify-reviewer` subagent 角色规范和 `.ai/quality/simplify-*.md` 报告产物。

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

> 当前 `java` 分支提供 Java Spring Boot 后端支持。
