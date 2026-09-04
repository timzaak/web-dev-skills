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

在实现、测试和 Demo 验收完成后，基于 `.ai/prd/<domain>/<feature>.md` 草稿、`.ai/user-stories/<domain>/<feature>.md` draft 用户故事、现有正式 PRD / 用户故事和实现后证据，先总结"草稿提出了什么、最终交付了什么、现有正式文档缺什么或哪里过期"，再修正增补现有 `docs/prd/<domain>/<feature>.md` 和 `docs/user-stories/**/*.md`。没有正式 PRD 或合适用户故事文件时才创建。完成后删除对应 `.ai/prd` 和 `.ai/user-stories` 草稿。

输出文件：
- `docs/prd/<domain>/<feature>.md`
- 可能更新：`docs/prd/00-index.md`、`docs/user-stories/**/*.md`

## 核心约束

- 固定在实现、测试和 Demo 验收完成之后运行；缺少完成证据时停止。
- 核心动作是先做发布总结并获用户确认，再修正增补现有正式文档；以差异归纳和事实合并为主，只把仍然成立、且属于长期产品语义的内容写入 `docs/prd`。
- 正式 PRD 内容聚焦产品语义；端点明细、schema、建表、代码类型和实施进度状态留在设计、任务或实现证据中。
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

### 1. 校验参数与定位草稿

- 检查 `[feature]` 非空且符合文件名规则（英文、数字、空格、下划线、连字符）
- 在 `.ai/prd/**/*.md` 中按文件名精确匹配 `[feature]`；多个 domain 匹配时停止并让用户选择
- 目标路径固定为 `docs/prd/<domain>/<feature>.md`

### 2. 发布前检查与发布摘要确认

读取草稿、正式 PRD、索引、相关用户故事、设计和验收报告（`.ai/task/<feature>/.state.json` 如存在，仅用于理解实现阶段背景；发布判断以 PRD 草稿、正式文档、设计、质量报告、Demo 验收和交付证据为准）。检查并形成结论：

- 草稿核心章节完整性、PRD 内容边界符合性；draft 用户故事的 INVEST、GWT 和内容边界
- 草稿引用的用户故事是否存在；草稿、draft 用户故事、正式 PRD / 用户故事和实现后证据的一致性与已说明差异
- PRD 和设计是否覆盖仍然有效的 Active Decision，且没有把 Superseded Decision 发布为当前事实
- 是否存在 `Must Resolve Before=t-prd-publish` 或更早但尚未解决的 Deferred Question；存在时先完成用户裁决
- 现有正式 PRD / 用户故事的缺失、过期或与已交付产品语义不一致问题
- 草稿中哪些内容应写入、删去、降级或仅作为发布摘要说明；draft 用户故事中哪些应追加、合并、改写、删去或仅作摘要说明；索引是否需要新增或更新条目
- 是否已有实现、测试和 Demo 验收完成证据

发现 P0 问题或缺少完成证据时停止发布并输出修复建议。

通过后先向用户展示发布摘要并用 `AskUserQuestion` 请求确认：草稿路径与目标路径、修正增补类型（revise / append / create-if-missing）、与现有正式 PRD / 用户故事的关键差异、草稿与实现后证据的对齐结论、将写入的长期产品事实与用户故事的角色/场景/验收标准、用户故事引用变化、索引更新计划、阻塞风险或"无"。未获得确认则结束本轮发布。

### 3. 写入正式文档

用户确认后：
- 基于草稿、正式 PRD 和实现后证据，修正/增补 `docs/prd/<domain>/<feature>.md` 和 `docs/user-stories/**/*.md`；保留仍有效的既有内容，只修正缺失、过期、冲突或需增补的部分；新增或合并 draft story 时保持角色引用、INVEST 和 GWT 验收标准
- 写入内容采用当前产品能力、业务规则或验收目标表述，避免用"已完成/已实现/本次交付"等实施进度表述承载长期事实
- 目标正式 PRD 不存在时才创建；如索引存在，更新 `docs/prd/00-index.md` 对应条目（遵循目标项目现有索引文件）
- 删除 `.ai/prd/<domain>/<feature>.md` 和 `.ai/user-stories/<domain>/<feature>.md`（如存在）；对应空目录可一并删除
- 保留 `.ai/decision-log/<feature>.md` 供本轮后续追溯；不得随 PRD 草稿一起删除

### 4. 发布后验证

- 重新检查正式 PRD 可读且路径正确
- 确认对应 `.ai/prd` 草稿已不存在；`.ai/user-stories` 草稿已不存在或本轮本就不存在

## 收尾输出

完成后明确说明：修正增补类型、正式 PRD 路径、正式用户故事更新路径（如有）、已删除的草稿路径、是否更新索引、发布后建议命令（`/t-prd-check [feature]` 做正式 PRD 校验；通过后可进入 `/t-release [version]`）。

## 失败处理

- 草稿不存在 → 提示先执行 `/t-prd [feature]`；多个草稿匹配 → 停止并要求用户指定 feature/domain
- 草稿或 draft 用户故事存在 P0 问题 → 停止并列出必须修复项
- 缺少实现、测试或 Demo 验收完成证据 → 停止并提示先完成对应阶段
- 用户未确认发布 → 结束本轮发布
- 写入失败 → 报告路径和错误，保留草稿
- 正式 PRD 或用户故事写入成功但草稿删除失败 → 报告为收尾失败，要求用户手动处理该草稿
