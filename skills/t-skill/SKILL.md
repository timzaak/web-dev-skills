---
name: t-skill
description: Create or update a skill — by default inside the t-tools plugin repository; with --project inside the current target project's skill directory. Use when adding a new t-* command, turning a repeated workflow into a skill, or changing an existing skill's responsibility, structure, or trigger description. Not for regular target-project feature work; skills already planned as t-super-run/t-task deliverables follow the task's own agent context.
argument-hint: "[--project] [<skill-name> | 能力描述]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
  - Agent
---

# Skill 创作

创建与更新共用流程；微调只需定位编辑与验证。

## 参数与模式路由

| 模式 | 落位与命名 | 规则归属 | 验证与同步 |
| --- | --- | --- | --- |
| 默认：插件模式 | `${CLAUDE_PLUGIN_ROOT}/skills/`，名称加 `t-` 前缀 | 按仓库 AGENTS.md 分配到 skill、agent、protocol、guide、script，并同步消费者及相关索引 | 运行 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/check-markdown-links.py`；命令入口变化时同步 t-how 和中英文 README |
| `--project`：项目模式 | 项目 `.claude/skills/` 或 `.agents/skills/`，沿用项目命名 | 遵守项目 AGENTS.md；无其他约定时收敛在 skill 目录内 | 核对引用文件存在，只写选定的 skill 根目录 |

项目模式恰有一个既有 skill 根目录时直接使用；没有或多个并存时用 AskUserQuestion 选定（也可由用户指定全局目录），全程保持。产物默认自足，使用相对路径引用内部资源；确需依赖插件时用 `${CLAUDE_PLUGIN_ROOT}` 并声明依赖前提。项目与插件约束冲突时按 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md` 报告冲突，不静默覆盖。

参数为已有 skill 名时更新，否则按名称或能力描述新建；目标不明时先从当前对话提取，仍无法确定再询问。名称冲突且用户要求新建时，请用户选择更新或另起名称。

## 工作流

### 1. 确认边界与查重

明确能力、触发边界、成功条件、输入输出及下游消费方；涉及状态时确认恢复与重复执行行为。优先使用对话和仓库事实，更新只核对差异，不重复访谈；需要用户裁决的缺口不写成已确认事实。

在选定根目录的 `*/SKILL.md` 中搜索同类能力，职责重叠时列出证据，由用户选择扩展或新建。

### 2. 编写

修改前读取 [skill 写作准则](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-authoring.md)，按其中的结构、命名、引用和更新规则编写 `<根目录>/<name>/SKILL.md`，按需补 references/scripts；模式差异遵循上表。

### 3. 验证与交付

- 按下列门禁自检，并完成模式表中的验证与同步；失败先修复，保留已完成产物，修复后从失败项继续。
- 新增或修改脚本时直接运行，并覆盖受影响的错误路径。
- 新建或结构性大改时，读取 [skill 测试与迭代](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-testing.md) 按风险验证；微调可只做自检和引用核对。项目模式使用目标项目上下文，测试产物放隔离临时目录并在结束后清理。
- 报告实际路径、变更、验证结果与未完成项；未过门禁不宣称完成。

## 质量门禁

- `description` 说明能力、触发条件与相邻入口边界；`name` 与目录名一致。
- 内容影响实际决策，引用注明读取时机且可达，无占位或无用途资源；插件内部引用使用 `${CLAUDE_PLUGIN_ROOT}`。
- 产物说明来源、位置、成功条件和消费方；持久状态说明转换、恢复点、重复执行行为与失败后的继续方。
- 无未确认假设，写入范围符合模式约束，验证与同步已完成。
