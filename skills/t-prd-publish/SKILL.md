---
name: t-prd-publish
description: After implementation and acceptance, summarize the draft PRD against delivered facts, then revise the existing formal PRD.
argument-hint: "[feature-name]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
  - Bash
---

# PRD 发布总结与正式文档修正

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（判断产物写入位置或脚本入口与插件默认冲突时读）
需求来源边界：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`（区分草稿与已发布需求来源或处理两者冲突时读）
决策连续性和用户决策暴露：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`（提问、更新决策账本或处理决策暴露门禁时读）

若草稿、正式 PRD、用户故事或规范之间冲突，以明确澄清为继续条件：停止、说明冲突并等待决策。

## 目标

在实现、测试和 Demo 验收完成后，基于 `.ai/prd/<domain>/<feature>.md` 草稿、`.ai/user-stories/<domain>/<feature>.md` draft 用户故事、现有正式 PRD / 用户故事和实现后证据，先总结“草稿提出了什么、最终交付了什么、现有正式文档缺什么或哪里过期”，再修正增补现有 `docs/prd/<domain>/<feature>.md` 和 `docs/user-stories/**/*.md`。没有正式 PRD 或合适用户故事文件时才创建。完成后删除对应 `.ai/prd` 和 `.ai/user-stories` 草稿。

该 skill 聚焦“代码实现后，如何把通过草稿沉淀的新需求同步回长期 PRD”。输出应体现已稳定的产品事实、业务规则、用户场景和验收目标。

输出文件：
- `docs/prd/<domain>/<feature>.md`
- 可能更新：`docs/prd/00-index.md`
- 可能更新：`docs/user-stories/**/*.md`

## 核心约束

- 固定在实现、测试和 Demo 验收完成之后运行，服务于实现后的正式文档发布。
- 核心动作是先做发布总结，再修正增补现有正式 PRD；正式 PRD 不存在时才创建。
- 发布总结用于确认写入范围；长期 PRD 只沉淀稳定产品事实。
- 以差异归纳和事实合并为主；只把仍然成立、且属于长期产品语义的内容写入 `docs/prd`。
- 写入前先摘要：草稿、正式 PRD、实现后证据之间的差异，现有正式 PRD 需要修正的问题，索引影响和风险项；用户确认后才写入。
- 发布后删除对应 `.ai/prd/<domain>/<feature>.md` 和 `.ai/user-stories/<domain>/<feature>.md`（如存在）。
- 正式 PRD 内容聚焦产品语义，端点明细、schema、建表、代码类型和实现进度状态留在设计、任务或实现证据中。
- 缺少实现、测试或 Demo 验收证据时停止。
- 发布范围限定为正式 PRD、正式用户故事、PRD 索引和草稿清理。

## Input Contract

必须读取：
- `.ai/prd/<domain>/<feature>.md` — 待发布 PRD 草稿
- `.ai/user-stories/<domain>/<feature>.md` — 待发布 draft 用户故事（如存在）
- `docs/prd/<domain>/<feature>.md` — 已发布正式 PRD（如存在）
- `docs/prd/00-index.md` — 正式 PRD 索引（如存在）
- `docs/user-stories/**/*.md` — 草稿引用的用户故事
- `.ai/design/<feature>.md` — 相关技术设计（如存在）
- `.ai/decision-log/<feature>.md` — 跨阶段决策账本（存在时必须读取）
- `.ai/task/<feature>/.state.json` — 可选实现阶段背景材料（如存在）
- `${CLAUDE_PLUGIN_ROOT}/guides/product/prd.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/prd-check-rubric.md`

如果找不到草稿，立即失败并提示先执行 `/t-prd [feature]`。

## 工作流程

### 1. 校验参数

- 检查 `[feature]` 非空且符合文件名规则
- 文件名仅允许英文、数字、空格、下划线、连字符

### 2. 定位草稿和目标

- 在 `.ai/prd/**/*.md` 中按文件名精确匹配 `[feature]`
- 如多个 domain 匹配，停止并让用户选择一个明确路径
- 目标路径固定为 `docs/prd/<domain>/<feature>.md`

### 3. 发布前检查

读取草稿、正式 PRD、索引、相关用户故事、设计和验收报告；如 `.ai/task/<feature>/.state.json` 存在，可用于理解实现阶段背景。发布判断以 PRD 草稿、正式文档、设计、质量报告、Demo 验收和交付证据为准。检查：
- 草稿核心章节是否完整
- 草稿引用的用户故事是否存在
- draft 用户故事是否符合 INVEST、GWT 和内容边界规则
- 草稿内容是否符合 PRD 内容边界
- 草稿、draft 用户故事、正式 PRD / 用户故事和实现后证据的一致性与已说明差异
- PRD 和设计是否覆盖仍然有效的 Active Decision，且没有把 Superseded Decision 发布为当前事实
- 是否存在 `Must Resolve Before=t-prd-publish` 或更早但尚未解决的 Deferred Question；存在时先完成用户裁决
- 现有正式 PRD / 用户故事是否存在缺失、过期或与已交付产品语义不一致的问题
- 草稿中哪些内容应写入、删去、降级或仅作为发布摘要说明
- draft 用户故事中哪些故事应追加、合并、改写、删去或仅作为发布摘要说明
- `docs/prd/00-index.md` 是否需要新增或更新条目
- 是否已有实现、测试和 Demo 验收完成证据

如果发现 P0 问题或缺少完成证据，停止发布并输出修复建议。

### 4. 生成发布摘要并确认

写入前先向用户展示：
- 草稿路径和目标正式 PRD 路径
- 修正增补类型：revise / append / create-if-missing
- 与现有正式 PRD 的关键差异
- 与现有正式用户故事的关键差异
- 草稿内容与实现后证据的对齐结论
- 现有正式 PRD / 用户故事需要修正的问题清单
- 将写入正式 PRD 的长期产品事实
- 将写入正式用户故事的角色、场景和验收标准
- 正式 PRD 内容边界：实施过程、临时状态和技术细节归属设计、任务或实现证据
- 用户故事引用变化
- 实现与验收完成证据摘要
- 索引更新计划
- 阻塞风险或"无"

使用 `AskUserQuestion` 请求确认。获得确认后进入正式文档写入；未获得确认则结束本轮发布。

### 5. 写入正式 PRD

用户确认后：
- 基于草稿、正式 PRD 和实现后证据，修正/增补 `docs/prd/<domain>/<feature>.md`
- 基于 draft 用户故事、正式用户故事和实现后证据，修正/增补 `docs/user-stories/**/*.md`
- 保留正式 PRD 中仍然有效的既有内容，只修正缺失、过期、冲突或需要增补的部分
- 保留正式用户故事中仍然有效的既有故事；新增或合并 draft story 时保持角色引用、INVEST 和 GWT 验收标准
- 写入内容采用当前产品能力、业务规则或验收目标表述，避免用“已完成/已实现/本次交付”等实施进度表述承载长期事实
- 目标正式 PRD 不存在时，才创建 `docs/prd/<domain>/<feature>.md`
- 如索引存在，更新 `docs/prd/00-index.md` 的对应条目；索引维护遵循目标项目现有索引文件
- 删除 `.ai/prd/<domain>/<feature>.md`
- 删除 `.ai/user-stories/<domain>/<feature>.md`（如存在）
- 保留 `.ai/decision-log/<feature>.md` 供本轮后续追溯；不得随 PRD 草稿一起删除
- 若 `.ai/prd/<domain>/` 删除草稿后为空，可删除该空目录
- 若 `.ai/user-stories/<domain>/` 删除草稿后为空，可删除该空目录

### 6. 发布后验证

- 重新检查正式 PRD 是否可读且路径正确
- 确认对应 `.ai/prd/<domain>/<feature>.md` 已不存在
- 确认对应 `.ai/user-stories/<domain>/<feature>.md` 已不存在或本轮不存在 draft 用户故事

## 收尾输出

完成后明确说明：
- 修正增补类型
- 正式 PRD 路径
- 正式用户故事更新路径（如有）
- 已删除的草稿路径
- 是否更新索引
- 发布后建议命令：`/t-prd-check [feature]` 做正式 PRD 校验；通过后可进入 `/t-release [version]`

## 失败处理

- 草稿不存在 → 提示先执行 `/t-prd [feature]`
- 多个草稿匹配 → 停止并要求用户指定 feature/domain
- 草稿存在 P0 问题 → 停止并列出必须修复项
- draft 用户故事存在 P0 问题 → 停止并列出必须修复项
- 缺少实现、测试或 Demo 验收完成证据 → 停止并提示先完成对应阶段
- 用户未确认发布 → 结束本轮发布
- 写入失败 → 报告路径和错误，保留草稿
- 正式 PRD 或用户故事写入成功但草稿删除失败 → 报告为收尾失败，要求用户手动处理该草稿
