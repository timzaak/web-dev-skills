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

## 确认目标与写入边界

| 模式 | 落位与命名 | 规则归属 | 验证与同步 |
| --- | --- | --- | --- |
| 默认：插件模式 | 已核实的 t-tools 源码工作树下的 `skills/`，名称加 `t-` 前缀 | 按源码工作树的 AGENTS.md 归位，检查消费者和相关索引 | 从源码工作树根目录运行 `uv run scripts/check-markdown-links.py`，命令入口变化时同步 t-how 和中英文 README |
| `--project`：项目模式 | 项目 `.claude/skills/` 或 `.agents/skills/`，沿用项目命名 | 遵守项目 AGENTS.md；无其他约定时收敛在 skill 目录内 | 核对引用文件存在，只写选定的 skill 根目录 |

- 插件模式按用户指定的源码路径、当前目录、插件加载路径 `${CLAUDE_PLUGIN_ROOT}` 的顺序定位：运行 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/resolve-ttools-source.py [用户指定路径]`，由脚本验证候选并输出根目录与 revision。安装缓存只用于读取插件资源。脚本对所有候选核实失败时，询问源码路径并暂停写入。
- 项目模式使用用户指定的 skill 根目录（可为全局目录）或唯一既有的项目 skill 根目录。未指定且没有或存在多个根目录时，用 AskUserQuestion 选定后保持写入范围。内部资源用相对路径，确需依赖插件时用 `${CLAUDE_PLUGIN_ROOT}` 并声明前提。项目与插件约束冲突时按 [运行时边界](${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md) 报告冲突。

已有 skill 名默认更新，其余按名称或能力描述新建。用对话和仓库事实确定能力、触发边界、成功条件及受影响的输入输出。微调只核对差异。新增或改变职责时搜索同类入口。明确要求新建但名称已存在，或存在职责重叠时，列出证据并请用户选择扩展或另建。

## 编写

修改前读取 [skill 写作准则](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-authoring.md)，将可复用的判断写入 `<根目录>/<name>/SKILL.md` 或对应规则的维护位置，按需引用资源。插件模式从已核实的源码工作树读取写作和测试准则。影响用户意图或交付边界的未决事项先确认。

## 交付门禁

- 核对名称、触发边界、受影响的产物与状态契约、写入范围和资源引用。完成对应模式的检查与同步。
- 新建、结构性大改或修改触发描述时，按 [skill 测试与迭代](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-authoring.md) 验证受影响行为。其余微调可直接自检和核对引用。新增或修改脚本时直接运行，覆盖受影响的错误路径。
- 验证失败时保留已完成产物，修复后从失败项重试。报告实际路径、变更、验证结果和未完成项，所有适用门禁通过后才能报告完成。
