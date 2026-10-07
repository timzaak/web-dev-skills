---
name: t-skill
description: Create or update a skill inside the t-tools plugin repository. Use when adding a new t-* command, turning a repeated workflow into a skill, or changing an existing skill's responsibility, structure, or trigger description. Operates only on the plugin repo itself; not for target-project feature work.
argument-hint: "[<skill-name> | 能力描述]"
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

在 t-tools 仓库内创建或更新一个 skill：捕获意图、查重归位、定结构、写作、验证和行为测试。创建与更新共用入口，按工作量裁剪流程：微调只做定位编辑加验证，不重走全流程。

## 参数

- `$ARGUMENTS` 是 skill 名：`skills/<name>/` 已存在 → 更新模式，修改前先快照；不存在 → 新建模式
- `$ARGUMENTS` 是能力描述 → 从 Step 1 推导出名称后进入新建模式
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

- Glob `skills/*/SKILL.md` 并 grep 能力关键词；与既有 skill 职责重叠时，列出重叠点交用户裁决"扩展既有还是新建"，不擅自新建
- 按仓库 AGENTS.md「规则归属」决定每条规则落位：阶段编排进本 skill；单一角色执行或验收进 `agents/`；被多个入口使用的契约进 `protocols/`；工程规范进 `guides/`；确定性重复操作进 `scripts/`。同一规则只维护一份
- 新建或修改 protocol、guide、agent 时，按 AGENTS.md「修改前后检查」同步全部消费者，包括 `protocols/index.md` 索引

### Step 3: 定结构

- 必需产物只有 `skills/<name>/SKILL.md`（frontmatter + 正文）
- 正文放不下且按场景分头使用的内容才进 `references/`；确定性重复逻辑才进 `scripts/`
- 不创建空目录、占位文件和无用途示例
- 命名：`t-` 前缀 kebab-case、动词导向、简短；目录名与 `name` 一致

### Step 4: 写作

先读取 [skill 写作准则](${CLAUDE_PLUGIN_ROOT}/skills/t-skill/references/skill-writing-guide.md)，要点：

- `description` 同时说明做什么、何时使用，并与相邻 skill 消歧；"何时使用"信息不重复进正文
- 正文结构对齐仓库既有 skill：目标、适用范围、流程、质量门禁、失败处理、资源路由
- 分场景细节进 references 并注明何时读取；引用插件内文件一律用 `${CLAUDE_PLUGIN_ROOT}` 前缀
- 更新模式保留原 `name` 与目录名，不做版本化命名

### Step 5: 验证与同步

- 按「质量门禁」逐项自检
- 运行 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/check-markdown-links.py`，按报告消除死链和不可达文档
- 新增或修改了命令入口 → 同步 `skills/t-how/SKILL.md` 的场景路由表
- 本次新增或修改了脚本 → 直接运行脚本并覆盖错误路径

### Step 6: 行为验证

新建或结构性大改推荐执行，微调可跳过。先读取 [skill 测试与迭代](${CLAUDE_PLUGIN_ROOT}/skills/t-skill/references/skill-test-loop.md)：

- 用 2-3 个真实用户 prompt 起独立 subagent 前向测试，不给预期答案
- `description` 用 should-trigger 与 near-miss 用例验证触发边界
- 只按观察到的行为做窄修正，不过拟合测试样例

## 质量门禁

- `description` 覆盖做什么、何时使用、消歧三要素；`name` 与目录名一致
- 只保留会改变模型决策或执行结果的内容；无占位文件、无虚构引用、无未使用目录
- 每个引用都注明何时读取；插件内引用使用 `${CLAUDE_PLUGIN_ROOT}` 前缀
- 涉及阶段产物时写明输入来源、输出位置、成功条件和下游消费方
- 涉及持久化状态时写明状态转换、可恢复点、重复执行行为和失败后由谁继续
- 链接检查通过；t-how 路由表已同步
- 未向用户确认的假设没有写入产物

## 失败处理

- 参数指向已存在 skill 但用户意图是新建：向用户确认后走更新模式，或请用户给出新名称
- 职责与既有 skill 重叠：列重叠点交用户裁决，不默认新建
- 链接检查报告死链或不可达文档：修引用或补文件，不留死链
- 前向测试失败：先区分"skill 指令缺陷"与"测试 prompt 不现实"，只修前者
- 用户只想微调：跳过 Step 1-3，直接编辑并执行 Step 5

## 附加资源

- [skill 写作准则](${CLAUDE_PLUGIN_ROOT}/skills/t-skill/references/skill-writing-guide.md) — Step 4 动笔前读取
- [skill 测试与迭代](${CLAUDE_PLUGIN_ROOT}/skills/t-skill/references/skill-test-loop.md) — Step 6 行为验证时读取
