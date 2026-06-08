---
name: t-prd-publish
description: Review and publish a draft PRD from .ai/prd into docs/prd for one feature. Use when a draft PRD has passed review/check and needs to become the formal authoritative PRD source.
argument-hint: "[feature-name]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
  - Bash
---

# PRD 草稿发布

运行时边界统一参考：`protocols/runtime-boundaries.md`

若草稿、正式 PRD、用户故事或规范之间冲突，停止、说明冲突并等待澄清；不要平均折中。

## 目标

按 feature 将 `.ai/prd/<domain>/<feature>.md` 中已审阅的 PRD 草稿发布到 `docs/prd/<domain>/<feature>.md`，让 `docs/prd` 继续作为长期权威需求源。发布成功后删除对应 `.ai/prd` 草稿，避免临时候选内容长期干扰后续流程。

输出文件：
- `docs/prd/<domain>/<feature>.md`
- 可能更新：`docs/prd/00-index.md`

## 使用方式

```bash
/t-prd-publish [feature]
```

## 核心约束

- 发布单位固定为单个 feature，不自动批量发布最近变更。
- 发布模式固定为先审后写：先输出差异摘要、目标路径、索引影响和风险项；用户确认后才写入 `docs/prd`。
- `.ai/prd` 是临时候选源，`docs/prd` 是正式权威源；发布后不得在正式 PRD 中写入 `.ai/prd` 草稿路径作为需求依据。
- 发布成功后必须删除对应 `.ai/prd/<domain>/<feature>.md`；不得保留草稿历史。
- 发布前必须检查草稿是否符合 PRD 内容边界：不得包含端点明细、schema、数据库表结构、代码类型、技术设计承接或实现进度状态。
- 发布不得修改实现代码、设计文档、任务文档或 Demo。

## Input Contract

必须读取：
- `.ai/prd/<domain>/<feature>.md` — 待发布 PRD 草稿
- `docs/prd/<domain>/<feature>.md` — 已发布正式 PRD（如存在）
- `docs/prd/00-index.md` — 正式 PRD 索引（如存在）
- `docs/user-stories/**/*.md` — 草稿引用的用户故事
- `${CLAUDE_PLUGIN_ROOT}/guides/product/prd.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/prd-check-rubric.md`

如果找不到草稿，立即失败并提示先执行 `/t-prd [feature]`。

## 工作流程

### 1. 校验参数

- 检查 `[feature]` 非空且符合文件名规则
- 文件名仅允许英文、数字、空格、下划线、连字符
- 拒绝 `..`, `/`, `\`
- 长度限制 1 到 50 字符

### 2. 定位草稿和目标

- 在 `.ai/prd/**/*.md` 中按文件名精确匹配 `[feature]`
- 如多个 domain 匹配，停止并让用户选择一个明确路径
- 目标路径固定为 `docs/prd/<domain>/<feature>.md`

### 3. 发布前检查

读取草稿、正式 PRD、索引和相关用户故事，检查：
- 草稿核心章节是否完整
- 草稿引用的用户故事是否存在
- 草稿是否混入 PRD 禁止内容
- 草稿与现有正式 PRD 的目标、范围、规则、状态和验收目标是否存在未说明冲突
- `docs/prd/00-index.md` 是否需要新增或更新条目

如果发现 P0 问题，停止发布并输出修复建议。

### 4. 生成发布摘要并确认

写入前先向用户展示：
- 草稿路径和目标正式 PRD 路径
- 发布类型：create 或 update
- 与现有正式 PRD 的关键差异
- 用户故事引用变化
- 索引更新计划
- 阻塞风险或"无"

使用 `AskUserQuestion` 请求确认。未确认时不得写入 `docs/prd`。

### 5. 写入正式 PRD

用户确认后：
- 将草稿内容写入 `docs/prd/<domain>/<feature>.md`
- 如索引存在，更新 `docs/prd/00-index.md` 的对应条目；索引不存在时不强行创建
- 删除 `.ai/prd/<domain>/<feature>.md`
- 若 `.ai/prd/<domain>/` 删除草稿后为空，可删除该空目录

### 6. 发布后验证

- 重新检查正式 PRD 是否可读且路径正确
- 确认对应 `.ai/prd/<domain>/<feature>.md` 已不存在
- 运行或建议运行 `/t-html-show docs/prd/<domain>/<feature>.md` 生成正式 PRD Preview
- 建议运行 `/t-prd-check [feature]`

## 收尾输出

完成后明确说明：
- 发布类型：create 或 update
- 正式 PRD 路径
- 已删除的草稿路径
- 是否更新索引
- 发布后建议命令：`/t-prd-check [feature]`，通过后执行 `/t-design [feature]`

## 失败处理

- 草稿不存在 → 提示先执行 `/t-prd [feature]`
- 多个草稿匹配 → 停止并要求用户指定 feature/domain
- 草稿存在 P0 问题 → 停止并列出必须修复项
- 用户未确认发布 → 停止，不写入 `docs/prd`
- 写入失败 → 报告路径和错误，不删除草稿
- 正式 PRD 写入成功但草稿删除失败 → 报告为收尾失败，要求用户手动处理该草稿后再进入 `/t-design`

## 相关引用

- `skills/t-prd/SKILL.md`
- `skills/t-prd-check/SKILL.md`
- `skills/t-html-show/SKILL.md`
- `skills/t-design/SKILL.md`
