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

运行时边界统一参考：`protocols/runtime-boundaries.md`

若草稿、正式 PRD、用户故事或规范之间冲突，停止、说明冲突并等待澄清；不要平均折中。

## 目标

在实现、测试和 Demo 验收完成后，基于 `.ai/prd/<domain>/<feature>.md` 草稿、现有正式 PRD 和实现后证据，先总结“草稿提出了什么、最终交付了什么、现有正式 PRD 缺什么或哪里过期”，再修正增补现有 `docs/prd/<domain>/<feature>.md`。没有正式 PRD 时才创建。完成后删除对应 `.ai/prd` 草稿。

该 skill 解决的是“代码实现后，如何把通过草稿沉淀的新需求同步回长期 PRD”的问题。它不是实现报告生成器，也不是把 `.ai/prd` 直接复制到 `docs/prd`。

输出文件：
- `docs/prd/<domain>/<feature>.md`
- 可能更新：`docs/prd/00-index.md`

## 使用方式

```bash
/t-prd-publish [feature]
```

## 核心约束

- 固定在实现、测试和 Demo 验收完成之后运行；不得作为 `/t-design` 前置步骤。
- 核心动作是先做发布总结，再修正增补现有正式 PRD；正式 PRD 不存在时才创建。
- 发布总结只用于确认写入范围，不作为长期进度记录写入 PRD。
- 不得简单复制草稿；只把仍然成立、且属于长期产品语义的内容写入 `docs/prd`。
- 写入前先摘要：草稿、正式 PRD、实现后证据之间的差异，现有正式 PRD 需要修正的问题，索引影响和风险项；用户确认后才写入。
- 发布后删除对应 `.ai/prd/<domain>/<feature>.md`。
- 拟写入 PRD 的内容不得包含端点明细、schema、建表、代码类型或实现进度状态。
- 缺少实现、测试或 Demo 验收证据时停止。
- 发布不得修改实现代码、设计文档、任务文档或 Demo。

## Input Contract

必须读取：
- `.ai/prd/<domain>/<feature>.md` — 待发布 PRD 草稿
- `docs/prd/<domain>/<feature>.md` — 已发布正式 PRD（如存在）
- `docs/prd/00-index.md` — 正式 PRD 索引（如存在）
- `docs/user-stories/**/*.md` — 草稿引用的用户故事
- `.ai/design/<feature>.md` — 相关技术设计（如存在）
- `.ai/task/<feature>/.state.json` — 任务状态（如存在）
- `.ai/quality/**/*.md` — 相关 check / accept 报告（如存在）
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

读取草稿、正式 PRD、索引、相关用户故事、设计、任务状态和验收报告，检查：
- 草稿核心章节是否完整
- 草稿引用的用户故事是否存在
- 草稿是否混入 PRD 禁止内容
- 草稿、正式 PRD 和实现后证据是否存在未说明冲突
- 现有正式 PRD 是否存在缺失、过期或与已交付产品语义不一致的问题
- 草稿中哪些内容应写入、删去、降级或仅作为发布摘要说明
- `docs/prd/00-index.md` 是否需要新增或更新条目
- 是否已有实现、测试和 Demo 验收完成证据

如果发现 P0 问题或缺少完成证据，停止发布并输出修复建议。

### 4. 生成发布摘要并确认

写入前先向用户展示：
- 草稿路径和目标正式 PRD 路径
- 修正增补类型：revise / append / create-if-missing
- 与现有正式 PRD 的关键差异
- 草稿内容与实现后证据的对齐结论
- 现有正式 PRD 需要修正的问题清单
- 将写入正式 PRD 的长期产品事实
- 不会写入正式 PRD 的实现过程、临时状态或技术细节
- 用户故事引用变化
- 实现与验收完成证据摘要
- 索引更新计划
- 阻塞风险或"无"

使用 `AskUserQuestion` 请求确认。未确认时不得写入 `docs/prd`。

### 5. 写入正式 PRD

用户确认后：
- 基于草稿、正式 PRD 和实现后证据，修正/增补 `docs/prd/<domain>/<feature>.md`
- 保留正式 PRD 中仍然有效的既有内容，只修正缺失、过期、冲突或需要增补的部分
- 不写入“已完成/已实现/本次交付”等实施进度表述；如需表达交付后稳定事实，改写为当前产品能力、业务规则或验收目标
- 目标正式 PRD 不存在时，才创建 `docs/prd/<domain>/<feature>.md`
- 如索引存在，更新 `docs/prd/00-index.md` 的对应条目；索引不存在时不强行创建
- 删除 `.ai/prd/<domain>/<feature>.md`
- 若 `.ai/prd/<domain>/` 删除草稿后为空，可删除该空目录

### 6. 发布后验证

- 重新检查正式 PRD 是否可读且路径正确
- 确认对应 `.ai/prd/<domain>/<feature>.md` 已不存在
- 运行或建议运行 `/t-html-show docs/prd/<domain>/<feature>.md` 生成正式 PRD Preview
- 建议运行 `/t-prd-check [feature]` 对正式 PRD 做发布后校验

## 收尾输出

完成后明确说明：
- 修正增补类型
- 正式 PRD 路径
- 已删除的草稿路径
- 是否更新索引
- 发布后建议命令：`/t-prd-check [feature]` 做正式 PRD 校验；通过后可进入 `/t-release [version]`

## 失败处理

- 草稿不存在 → 提示先执行 `/t-prd [feature]`
- 多个草稿匹配 → 停止并要求用户指定 feature/domain
- 草稿存在 P0 问题 → 停止并列出必须修复项
- 缺少实现、测试或 Demo 验收完成证据 → 停止并提示先完成对应阶段
- 用户未确认发布 → 停止，不写入 `docs/prd`
- 写入失败 → 报告路径和错误，不删除草稿
- 正式 PRD 写入成功但草稿删除失败 → 报告为收尾失败，要求用户手动处理该草稿

## 相关引用

- `skills/t-prd/SKILL.md`
- `skills/t-prd-check/SKILL.md`
- `skills/t-html-show/SKILL.md`
- `skills/t-design/SKILL.md`
