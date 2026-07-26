# AGENTS.md

这个仓库是 Claude Code plugin `t-tools` 的源码仓库，不是业务项目。它的作用是把 AI 编程组织成可执行、可恢复、可验收的工程工作流，用 skill 编排阶段，用 subagent 分工执行，用 protocol 固化共享契约，用 guide 承载工程规范。

## 工作定位

- 面向目标项目使用时，标准入口是 `/t-tools:t-*` 命令，而不是让模型自由选择流程。
- 插件主链路是 `Decision -> PRD Draft / Tech Research（按主要未知项选择，可回环）-> [PRD Check] -> Design -> [Design Check] -> Task -> [Task Check] -> Run -> Demo Run -> Demo Accept -> PRD Publish -> Release`，方括号内为可选质量检查；纯技术且不改变业务逻辑的方案可由 Tech Research 直接进入 Design。
- 这个 plugin 的核心价值是统筹 AI 编程：把需求、设计、任务、实现、测试、验收和 Demo 交付拆成有边界、有状态、有门禁的阶段。
- 不要把本仓库当成目标项目来生成业务代码。目标项目运行时事实主要落在目标项目的 `docs/` 和 `.ai/` 中。

## 仓库职责边界

- `.claude-plugin/plugin.json` 是插件清单，描述插件名、目标技术栈和依赖。
- `skills/` 是工作流入口，负责阶段编排、前置校验、状态推进、产物写入和失败恢复。
- `agents/` 是 Claude Code subagent 角色定义，负责具体执行或只读验收。
- `protocols/` 是跨 skill 和 agent 共享的单一契约源，状态结构、输出结构、评分规则优先在这里维护。
- `guides/` 是工程规范和领域实践，不要把大段 guide 规则复制到 agent 或 skill 文档里。
- `scripts/` 是插件提供给目标项目或流程复用的脚本；改脚本时要关注调用入口和跨平台路径处理。
- `packages/playwright-unified-logger/` 是插件内置的 Playwright 日志辅助包，改动时按独立 npm package 对待。

## 修改原则

- 修改共享规则时，优先判断它属于 `protocols/`、`guides/`、`skills/` 还是 `agents/`，避免把同一规则复制到多个地方。
- 如果变更影响命令调用、skill 名称、完整工作流或安装方式，同步更新 `README.md` 和 `README.en.md`。
- 如果变更影响插件暴露能力或依赖，同步检查 `.claude-plugin/plugin.json`。
- 如果变更影响目标项目运行时文件结构，优先检查 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md` 和 `${CLAUDE_PLUGIN_ROOT}/skills/t-init/` 相关模板。
- Agent 文档应保持角色边界清晰：dev 可以实现，test 专注测试，accept 默认只读验收并输出证据。
- `t-prd-check`、`t-design-check`、`t-task-check` 是可选质量检查；复杂、高风险、多人协作或 AI 输出不稳定时推荐运行。accept 阶段仍是实现后的验收收口，不要弱化验收职责。

## 质量与验证

- Markdown 链接检查使用 `${CLAUDE_PLUGIN_ROOT}/scripts/check-markdown-links.py`。
- 发布流程由 `${CLAUDE_PLUGIN_ROOT}/scripts/release.py` 和 `/t-tools:t-release` 约束，语义版本文件不带 `v`，git tag 使用 `v` 前缀。
- `packages/playwright-unified-logger/` 的验证应在该 package 目录内运行 npm 脚本。
- 当前仓库可能存在用户未提交改动；不要回滚与当前任务无关的文件。

## 写作约定

- 中文文档是主说明，英文文档需要与中文文档保持语义一致。
- 文档应面向已经会使用 AI 编程工具的读者，直接说明边界、契约、流程和门禁；避免解释模型自己能从文件系统看到的目录枚举。
- 引用插件内部文件时，在面向目标项目的文档中优先使用 `${CLAUDE_PLUGIN_ROOT}` 语义路径。
