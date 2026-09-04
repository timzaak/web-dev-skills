---
name: t-prd-check
description: Validate draft PRD, published PRD baseline, and user stories for quality and consistency.
argument-hint: "[feature-name|--all]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
  - Bash
---

# PRD 草稿与 User Story Quality Check

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（判断产物写入位置或脚本入口与插件默认冲突时读）
需求来源边界：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`（区分草稿与已发布需求来源或处理两者冲突时读）
决策连续性和用户决策暴露：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`（提问、更新决策账本或处理决策暴露门禁时读）
评估目标、评分维度、问题分级与报告结构：`${CLAUDE_PLUGIN_ROOT}/protocols/prd-check-rubric.md`（评分或分级前读）

本检查为可选质量检查：未运行或未通过不阻断 `/t-design`，但报告必须明确继续下游的已知风险。

## 输入范围

- PRD 草稿：`.ai/prd/**/*.md`
- 决策账本：`.ai/decision-log/<feature>.md`（存在时必须读取）
- 已发布 PRD 基线：`docs/prd/**/*.md`
- Draft 用户故事：`.ai/user-stories/**/*.md`
- 已发布用户故事：`docs/user-stories/**/*.md`

## 执行流程

### 1. 确定检查范围

- 单功能优先按文件名匹配 `.ai/prd/**/*.md` 草稿；无草稿则检查 `docs/prd/**/*.md` 正式 PRD（发布后质量检查）；都不存在时提示检查功能名称或先运行 `/t-prd [feature]`
- `--all` 默认检查全部草稿；无草稿时再检查全部正式 PRD
- 用 `Glob` 发现目标文件并排除特殊文件

### 2. 读取角色定义

读取 `docs/user-stories/_roles.md`，解析角色名称和技术标识，用于校验故事中的角色引用。

### 3. 评分与问题分级

全部按 `${CLAUDE_PLUGIN_ROOT}/protocols/prd-check-rubric.md` 执行：

- 先过 Decision Closure Gate：运行 `check-decision-closure.py`，`needs_user_answer` 未解决时用 `AskUserQuestion` 阻塞提问；用户回答写入 Decision Log 后，先由 `/t-prd [feature]` 更新 PRD，重新扫描通过后再继续检查
- 按 PRD Score / User Story Score 维度表逐项检查，并执行一致性门禁
- 对 `.ai/user-stories` 与 `docs/user-stories` 分别标注 draft / published 来源
- draft 与已发布基线的差异分类：补充新场景且不冲突记为 publish 候选；修改已发布语义必须识别差异性质；严重度按 rubric 的 P0/P1 定义

### 4. 输出

- 控制台摘要与详细报告结构按 rubric 的 Output Requirements；报告写入 `.ai/quality/prd-check-[YYYYMMDD-HHMMSS].md`
- 通过时建议下一步 `/t-design [feature]`；未通过或修复后建议重新运行 `/t-prd-check [feature]`

## 失败处理

- 文件解析错误：记录错误并继续其他文件
- 报告目录不存在：使用 `Bash` 创建 `.ai/quality/`
