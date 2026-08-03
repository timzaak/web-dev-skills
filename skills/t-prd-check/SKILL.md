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

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
需求来源边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`
决策连续性和用户决策暴露统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`

## 目标
- 验证 `.ai/prd` PRD 草稿完整性和规范性
- 评估用户故事质量（INVEST 原则、GWT 格式）
- 检查 PRD 与用户故事的一致性
- 检查 PRD 草稿与 `docs/prd` 已发布基线是否存在未说明冲突
- 检查 `.ai/user-stories` draft 与 `docs/user-stories` 已发布基线是否存在未说明冲突
- 检查 PRD / 用户故事是否错误混入接口、建表、schema 等实现细节
- 检查是否把需要用户回答的问题静默写成待确认、假设、风险或模糊占位
- 输出量化评分和修复清单
- 明确检查结论与风险；通过后建议进入 `/t-design [feature]`，未运行或未通过时用户仍可自行决定是否继续；若有修复，建议重新运行 `/t-prd-check [feature]`

评分、扣分和问题分级统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/prd-check-rubric.md`


## 输入范围
- PRD 草稿: `.ai/prd/**/*.md`
- 决策账本: `.ai/decision-log/<feature>.md`（存在时必须读取）
- 已发布 PRD 基线: `docs/prd/**/*.md`
- Draft 用户故事: `.ai/user-stories/**/*.md`
- 已发布用户故事: `docs/user-stories/**/*.md`

## 执行流程

### 1. 确定检查范围
- 解析命令参数，确定单功能或全量检查
- 单功能优先在 `.ai/prd/**/*.md` 中按文件名匹配草稿；若无草稿，则检查 `docs/prd/**/*.md` 中的正式 PRD，用于发布后质量检查
- 单功能下草稿和正式 PRD 都不存在时，提示检查功能名称或先运行 `/t-prd [feature]`
- `--all` 默认检查 `.ai/prd/**/*.md` 中的全部草稿；若没有草稿，再检查 `docs/prd/**/*.md` 中的正式 PRD
- 使用 `Glob` 发现目标文件并排除特殊文件

### 2. 读取角色定义
- 读取 `docs/user-stories/_roles.md`
- 解析角色名称和技术标识，用于校验故事中的角色引用

### 3. PRD 草稿检查
按 `${CLAUDE_PLUGIN_ROOT}/protocols/prd-check-rubric.md` 执行：

- 先运行 `python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py <prd-path>`
- 对命中项按 Decision Exposure Gate 分类
- 若存在 `needs_user_answer`，先查 Decision Log；未解决时立即使用 `AskUserQuestion`，回答前不评分、不生成通过结论
- 用户回答后先写入 Decision Log，再停止并要求运行 `/t-prd [feature]` 更新拥有产品事实的 PRD；PRD 修正并重新扫描通过后再继续检查
- 基础章节检查
- 用户故事引用检查
- PRD 分层与禁止内容检查
- 如果存在同名正式 PRD，记录草稿与正式 PRD 的关键差异
- 如果引用 `.ai/user-stories`，确认其为候选来源且路径存在

### 4. 用户故事检查
按 `${CLAUDE_PLUGIN_ROOT}/protocols/prd-check-rubric.md` 执行：

- 故事结构检查
- INVEST 原则检查
- 禁止内容检测
- 新文档质量门禁检查
- 对 `.ai/user-stories` 与 `docs/user-stories` 分别标注 draft / published 来源
- 若 draft story 与 published story 在角色、权限、目标、业务状态或验收目标上冲突且未说明覆盖关系，按一致性问题分级

### 5. 一致性检查
- 检查 PRD 中的用户故事链接是否有效
- 比较 PRD 与用户故事中的优先级是否一致
- 校验用户故事中的角色是否存在于 `_roles.md`
- 比较 `.ai/user-stories/<domain>/<feature>.md` 与相关 `docs/user-stories/**/*.md`：
  - draft story 补充新场景且不冲突 → 记录为 publish 候选
  - draft story 修改已发布故事语义 → 必须能识别差异性质
  - draft story 与已发布故事有未说明冲突 → P1；若冲突会改变核心角色、权限或验收目标 → P0
- 比较 `.ai/prd/<domain>/<feature>.md` 与 `docs/prd/<domain>/<feature>.md`：
  - 草稿对应正式 PRD 不存在 → 记录为 create-if-missing 候选
  - 草稿修改已发布 PRD → 必须能识别目标、范围、规则、状态或验收目标的差异
  - 草稿与正式 PRD 有未说明冲突 → P1；若冲突会改变核心业务边界或权限规则 → P0

### 6. 评分计算
按 `${CLAUDE_PLUGIN_ROOT}/protocols/prd-check-rubric.md` 计算：

- `PRD Score`
- `User Story Score`
- `Consistency Score`
- `Total Score`


### 7. 输出要求
- 控制台摘要和报告结构统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/prd-check-rubric.md`
- 详细报告文件：`.ai/quality/prd-check-[YYYYMMDD-HHMMSS].md`
- 通过时建议下一步为 `/t-design [feature]`
- 未运行或未通过本检查不阻断 `/t-design`，但报告必须明确继续下游的已知风险
- 未通过或修复后，建议再次运行 `/t-prd-check [feature]`
- 报告必须给出用户澄清状态、Decision Log 路径和决策闭合扫描结果

### 8. 失败处理
- 未找到 PRD 文档：提示检查功能名称或先运行 `/t-prd [feature]`
- 文件解析错误：记录错误并继续其他文件
- 报告目录不存在：使用 `Bash` 创建 `.ai/quality/`
