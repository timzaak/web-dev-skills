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

在 t-tools 插件仓库或当前目标项目内创建或更新一个 skill：捕获意图、查重归位、定结构、写作、验证和行为测试。创建与更新共用入口，按工作量裁剪流程：微调只做定位编辑加验证，不重走全流程。

## 参数与模式路由

| 参数 | 模式 | 操作对象 |
| --- | --- | --- |
| `[<skill-name> \| 能力描述]`（默认） | 插件模式 | t-tools 插件仓库 `skills/`，遵守仓库 AGENTS.md 的规则归属 |
| `--project [<skill-name> \| 能力描述]` | 项目模式 | 当前目标项目的 skill 根目录，落位与归位见「项目模式」 |

- 两模式共用下文 Step 1-6 主流程，差异集中在 Step 2、Step 5 和「项目模式」一节，其余步骤不按模式分叉
- 参数是 skill 名且在对应 skill 根目录已存在 → 更新模式，修改前先快照；不存在 → 新建模式
- 参数是能力描述 → 从 Step 1 推导出名称后进入新建模式
- 省略 → 用 AskUserQuestion 确认目标：新建什么、更新哪个，或把当前对话中的哪段流程沉淀为 skill

## 工作流

### Step 1: 捕获意图与边界

更新模式只核对现状与用户意图的差异，跳过访谈。

- 当前对话已含可沉淀的工作流时，先从对话提取：用过的工具、步骤顺序、用户的纠正、输入输出格式；缺口再问用户
- 只问影响结构的问题：
  1. 这个 skill 要让模型做成什么，成功条件是什么
  2. 何时触发、何时不应触发；最容易混淆的相邻 skill 是谁
  3. 输入来自哪里，产物写到哪，下游谁消费
  4. 是否涉及持久化状态、失败恢复和重复执行
- 无法从对话或仓库推断的缺口必须暴露给用户，不得把未确认假设写入产物

### Step 2: 查重与规则归位

- 查重范围按模式：插件模式 Glob `${CLAUDE_PLUGIN_ROOT}/skills/*/SKILL.md`；项目模式 Glob 选定 skill 根目录下的 `*/SKILL.md`。grep 能力关键词，与既有 skill 职责重叠时，列出重叠点交用户裁决"扩展既有还是新建"，不擅自新建
- 插件模式按仓库 AGENTS.md「规则归属」决定每条规则落位：阶段编排进本 skill；单一角色执行或验收进 `agents/`；被多个入口使用的契约进 `protocols/`；工程规范进 `guides/`；确定性重复操作进 `scripts/`。同一规则只维护一份。新建或修改 protocol、guide、agent 时，按「修改前后检查」同步全部消费者，包括 `protocols/index.md` 索引
- 项目模式的规则归位见「项目模式」，不做插件仓库的归位和索引同步

### Step 3: 定结构

- 必需产物只有 `<skill 根目录>/<name>/SKILL.md`（frontmatter + 正文）
- 正文放不下且按场景分头使用的内容才进 `references/`；确定性重复逻辑才进 `scripts/`
- 不创建空目录、占位文件和无用途示例
- 命名：kebab-case、动词导向、简短；目录名与 `name` 一致。插件模式加 `t-` 前缀；项目模式不强制前缀，尊重项目既有命名

### Step 4: 写作

先读取 [skill 写作准则](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-authoring.md)，要点：

- `description` 同时说明做什么、何时使用，并与相邻 skill 消歧；"何时使用"信息不重复进正文
- 正文结构对齐目标仓库既有 skill：目标、适用范围、流程、质量门禁、失败处理、资源路由
- 分场景细节进 references 并注明何时读取
- 更新模式保留原 `name` 与目录名，不做版本化命名

### Step 5: 验证与同步

- 按「质量门禁」逐项自检
- 插件模式运行 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/check-markdown-links.py`，按报告消除死链和不可达文档；项目模式逐个核对正文引用的 references/scripts 路径实际存在，不依赖项目未必具备的检查脚本
- 插件模式新增或修改了命令入口 → 同步 `skills/t-how/SKILL.md` 的场景路由表；项目模式不修改插件仓库
- 本次新增或修改了脚本 → 直接运行脚本并覆盖错误路径（两模式相同）

### Step 6: 行为验证

新建或结构性大改推荐执行，微调可跳过。先读取 [skill 测试与迭代](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-testing.md)：

- 用 2-3 个真实用户 prompt 起独立 subagent 前向测试，不给预期答案
- `description` 用 should-trigger 与 near-miss 用例验证触发边界
- 只按观察到的行为做窄修正，不过拟合测试样例
- 项目模式的测试在目标项目上执行

## 项目模式

`--project` 下的落位、归位与边界规则：

- **落位解析**：依次探测当前项目 `.claude/skills/`（Claude Code）与 `.agents/skills/`（open agent skills 约定）；恰好一个存在 → 直接使用；都不存在或多个并存 → 用 AskUserQuestion 选定根目录（可含全局 `~/.agents/skills/`），选定后全程保持，不中途切换
- **规则归位**：目标项目没有 protocols/agents 分层，规则默认收敛在 skill 目录内（SKILL.md + `references/` + 按需 `scripts/`）；项目 AGENTS.md 另有归位约定时从其约定
- **约束优先级**：项目执行约束以目标项目 AGENTS.md 为准；与插件默认规范冲突时不静默覆盖，报告冲突并按 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md` 处理
- **引用规则**：skill 默认自足，不引用插件内部文件；确需引用时使用 `${CLAUDE_PLUGIN_ROOT}` 前缀并在正文写明该依赖前提
- **写入边界**：只写入选定的 skill 根目录，不改目标项目其他文件；测试产物放隔离临时目录，测完清理

## 质量门禁

- `description` 覆盖做什么、何时使用、消歧三要素；`name` 与目录名一致
- 只保留会改变模型决策或执行结果的内容；无占位文件、无虚构引用、无未使用目录
- 每个引用都注明何时读取；插件模式引用插件内文件一律 `${CLAUDE_PLUGIN_ROOT}` 前缀，项目模式默认项目相对路径
- 涉及阶段产物时写明输入来源、输出位置、成功条件和下游消费方
- 涉及持久化状态时写明状态转换、可恢复点、重复执行行为和失败后由谁继续
- 插件模式：链接检查通过且 t-how 路由表已同步；项目模式：正文引用的文件全部实际存在且只写入了选定 skill 根目录
- 未向用户确认的假设没有写入产物

## 失败处理

- 参数指向已存在 skill 但用户意图是新建：向用户确认后走更新模式，或请用户给出新名称
- 职责与既有 skill 重叠：列重叠点交用户裁决，不默认新建
- 插件模式链接检查报告死链或不可达文档：修引用或补文件，不留死链；项目模式引用路径不存在：补文件或改引用，不留悬空引用
- 项目模式多个 skill 根目录并存且用户未裁决：AskUserQuestion 后继续，不默认猜测
- 前向测试失败：先区分"skill 指令缺陷"与"测试 prompt 不现实"，只修前者
- 用户只想微调：跳过 Step 1-3，直接编辑并执行 Step 5

## 附加资源

- [skill 写作准则](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-authoring.md) — Step 4 动笔前读取
- [skill 测试与迭代](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-testing.md) — Step 6 行为验证时读取
