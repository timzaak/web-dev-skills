# T-Tools

[English](README.en.md)

面向 Rust + React 项目的 Claude Code plugin。它把 `Decision -> 技术预研 -> PRD -> 设计 -> 任务 -> 开发 -> 验收 -> Demo` 串成一套可复用工作流，让你不用反复设计 prompt、切换上下文或手工维护阶段边界。

适合这类团队和项目：

- 已经有明确的产品文档、设计、任务拆解、开发、测试、Demo 交付链路
- 希望把 Claude Code 从"临时问答"升级成"可执行的工程工作流"
- 需要 sub-agent 分工、阶段门禁、标准化产物，而不是一次性自由发挥

## 为什么用它

- 上手快：直接按 `/t-tools:t-*` 命令顺序推进，不需要自己设计整套提示词和协作流程
- 交付稳：关键阶段自带检查和验收命令，减少文档跑偏、任务漏拆、Demo 不可执行
- 协作清：skill、agent、guide、protocol 已分层，适合多人或长期项目持续复用
- 人参与：关键产物不是交给 AI 一次生成后直接下游使用，而是通过 Preview、口述反馈、check / accept 让人持续校准需求意图、细节偏好和验收标准

## 设计思路导读

推荐先读 [human/structure.md](/human/structure.md)，理解 skill、subagent、protocol 如何协同驱动 AI 编程。

![T-Tools 知识图谱](knowledge-graph.png)

## 3 分钟快速上手

前置条件：

- 已按下方 [安装](#安装) 步骤加载 t-tools 插件
- 目标项目具备运行时目录：`docs/`、`.ai/`
- 已启用 [`context7`](https://github.com/upstash/context7)

最短闭环示例：

```bash
# 先判断这个 feature 是否值得进入后续流程，并打开 HTML 供审阅
/t-tools:t-decision user-management

# 需要技术可行性、依赖或成本判断时，先做技术预研
/t-tools:t-tech-research user-management

# 创建或更新 .ai/prd 与 .ai/user-stories 草稿，并打开 HTML 供审阅
/t-tools:t-prd user-management

# 人先口述自己认可的 PRD，再看 HTML Preview，并让 AI 对照修正

# 质量门禁：避免把问题带入设计阶段
/t-tools:t-prd-check user-management

# 基于 PRD 产出技术设计；纯技术方案也可基于 t-tech-research 产出
/t-tools:t-design user-management

# 人从用户视角梳理前端 UX 交互和体验取舍，明确告诉 AI 什么是好的 UX

# 把设计转换成可执行任务
/t-tools:t-task user-management

# 检查任务拆分、依赖和可执行性
/t-tools:t-task-check user-management --phase backend

# 按阶段驱动实现与测试
/t-tools:t-run user-management --phase backend

# 代码审查
/t-tools:t-code-review

# 运行该角色的 Demo/E2E 测试
/t-tools:t-demo-run super-admin

# 最终验收：确认故事映射、编译、执行和质量要求都通过
/t-tools:t-demo-accept super-admin

# 实现与验收完成后，基于草稿做发布总结并修正正式 PRD / 用户故事
/t-tools:t-prd-publish user-management
```

如果你只想记住一件事：不要跳过 check / accept 阶段。这个 plugin 的价值不只是"帮你生成内容"，而是"帮你在每个阶段收口"。

尤其在 `/t-tools:t-prd` 之后，不要直接进入 `/t-tools:t-prd-check`，也不要马上去看生成的 HTML Preview。人应先脱离生成物，自己口述或过一遍认可的 PRD：这个功能到底想解决什么、哪些路径最重要、哪些边界或异常必须考虑、哪些表达不符合预期。然后再打开 HTML Preview 做对照，让 AI 拿这段反馈和 PRD / Preview 定向修正。否则，人很容易被生成物带偏；即使有 HTML 帮助，也未必能快速抓住真正重点。不管模型能力多强，PRD 都容易滑向随机、普通、泛化的输出，细节性诉求也更容易被漏掉。

同样，在 `/t-tools:t-design` 之后，人必须站在用户角度梳理一遍前端 UX 交互：用户从哪里进入、每一步看到什么、如何判断下一步、哪些反馈必须即时出现、哪些默认值和错误状态会影响信任。好的 UX 不是模型自动推导出的客观答案，而是一种品味和取舍；需要明确告诉 AI 哪些体验是好的、哪些是不能接受的、你选择这种交互的原因是什么，再让 AI 对照技术设计修正。

补充说明：

- 本 README 统一使用 `/t-tools:t-*` 作为标准调用形式
- 本插件所有 `t-*` skill 均为手工触发入口，不允许模型根据语义自动触发
- `t-decision` 是 PRD 前的产品立项门禁，输出 `.ai/decision/<feature>.md` 和 `.ai/preview/decision/<feature>.html`；结论为 `Proceed` 或 `Research First` 后再进入技术预研或 PRD。它的交互方式借鉴 Garry Tan 的 [gstack](https://github.com/garrytan/gstack) 中 `office-hours` 与 `plan-ceo-review` 的产品诊断和 CEO review 思路，但已转译为 t-tools 的阶段门禁，不 vendoring gstack 运行时
- `t-prd` 只写 `.ai/prd` 和 `.ai/user-stories` 候选需求，不直接写 `docs/prd` 或 `docs/user-stories`；`t-prd-publish` 才负责把仍然成立的长期产品事实合并回 `docs/`
- `t-doc` 用于项目文档、上手教程、API 参考、配置和部署说明，不用于 PRD、技术设计或只改某个文档片段
- `t-dream` 默认以只读 audit 方式整理 PRD、用户故事、设计/任务、实现事实与项目结构，减少过期、重复、冲突和误导性上下文累积；需要写入 PRD 治理时显式使用 `--govern-prd`
- `t-code-review` 参考 Claude Code 官方 `/code-review` 的本地 diff 审查方式，默认审查当前分支和工作区改动，只输出高置信 correctness bug 与明确适用的规则违反；传 `--comment` 时才尝试评论 GitHub PR
- `t-push` 在提交前由 AI 基于本次 diff 清理明显低价值代码注释，再总结 commit message，并调用 `${CLAUDE_PLUGIN_ROOT}/scripts/push.py` 运行受影响 CI、提交和推送
- `t-backend-test-run` 是内部执行型 skill，供 `backend-test` 等流程复用，不作为推荐的手动入口

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
- MCP Server [`context7`](https://github.com/upstash/context7) 已配置（用于查询第三方库文档）

使用 Codex、ZCode 等不支持 `claude --plugin-dir` 的工具时，见 [在其它 AI 编程工具中使用 t-tools](human/use-in-other-agents.md)：通过在 `~/.agents/skills/` 下放置一个路由 skill，把 `/t-tool <skill>` 指向 `git clone` 后的仓库目录。

## 使用本插件的项目

- [Herald](https://github.com/timzaak/herald) — 多租户认证与授权系统，支持单租户与多租户场景的认证服务
- [RMQTT-Things](https://github.com/timzaak/rmqtt-things) — 基于 RMQTT 的物联网物模型管理平台，支持设备管理、命令下发、OTA 升级与 TLS 证书签发
- [RWiki](https://github.com/timzaak/rwiki) — 基于 Wiki.js 数据的 AI 增强知识库，支持 Wiki 内容同步、语义搜索与智能问答

> Java 后端支持见 `java` 分支。
