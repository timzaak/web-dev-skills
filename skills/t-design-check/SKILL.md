---
name: t-design-check
description: Evaluate technical design documents for implementability, completeness, and consistency with a quantitative 100-point score.
argument-hint: "[方案名称]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Task
  - Write
  - Bash
---

# 技术设计质量检查

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
需求来源边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`
决策连续性和用户决策暴露统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`

## 目标
- 评估技术设计文档的可实施性、完整性与一致性。
- 给出可复查的 100 分量化结果。
- 输出 P0/P1/P2 修复清单。
- 给出明确的设计质量检查结论；本检查为可选，不作为 `/t-task` 的硬性前置。
- 发现必须由用户裁决的设计问题时，使用 `AskUserQuestion` 阻塞式提问，不得只写入问题清单后继续。

评分维度、严重级别和报告要求统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/design-check-rubric.md`

## 输入范围
- 设计文档：`.ai/design/[feature].md`
- 决策账本：`.ai/decision-log/[feature].md`（存在时必须读取）
- 需求来源：`.ai/user-stories/**/*.md`、`docs/user-stories/**/*.md`、`.ai/prd/**/*.md`、`docs/prd/**/*.md`、`.ai/tech-research/**/*.md`
- 规范来源：
  - `${CLAUDE_PLUGIN_ROOT}/guides/core/environment-and-testing-guide.md`
  - `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md`
  - `${CLAUDE_PLUGIN_ROOT}/guides/backend/development.md`
  - `${CLAUDE_PLUGIN_ROOT}/guides/frontend/development.md`
  - `${CLAUDE_PLUGIN_ROOT}/guides/flutter/development.md`（目标项目启用 Flutter 时）
  - `AGENTS.md`

## 执行流程
- 校验设计文档是否存在。
- 从设计文档提取引用的用户故事、PRD、技术预研、接口、数据库变更、前端范围、测试策略。
- 运行 `python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py .ai/design/[feature].md`，对命中项按 Decision Exposure Gate 分类。
- 核对 Decision Trace 是否覆盖所有影响设计的 Active Decision，且没有使用 Superseded Decision。
- 核对设计文档与需求来源的一致性。
- 若设计引用 `.ai/user-stories`，确认其为 draft 候选来源且路径存在；若同时存在相关 `docs/user-stories`，检查是否存在未说明冲突。
- 如果设计文档声明为纯技术方案且不涉及业务逻辑变动，可接受 `.ai/tech-research/[feature].md` 作为唯一需求来源；此时不得因缺少 PRD/用户故事扣 P0，但需要核对技术目标、约束、影响范围和风险是否一致。
- 核对设计文档与项目规范的一致性。
- 按 `${CLAUDE_PLUGIN_ROOT}/protocols/design-check-rubric.md` 检查 API、数据库、前端与测试策略。
- 评估设计方案的章节组织是否内聚：若同一业务闭环、同一数据模型或同一外部契约被拆分为多个独立章节，应在设计阶段合并，避免 `/t-task` 产出颗粒度过细的 item。
- 若发现 `${CLAUDE_PLUGIN_ROOT}/protocols/design-check-rubric.md` 定义的 `needs_user_answer`，先查 Decision Log；未解决时立即使用 `AskUserQuestion` 向用户提问。回答前不生成通过结论；回答后先更新 Decision Log 和设计文档、重新运行决策闭合扫描，再继续评分。
- 生成评分与问题清单。
- 输出下一步建议：通过或风险可接受时进入 `/t-task [feature]`；修复后可重新运行 `/t-design-check [feature]`。
- 写入报告：`.ai/quality/design-check-[feature]-[YYYYMMDD-HHMMSS].md`。

## 错误处理

| 错误码 | 触发条件 | 用户可见提示 | 恢复动作 |
|---|---|---|---|
| `DESIGN_DOC_MISSING` | 设计文档不存在 | 未找到设计文档 | 先运行 `/t-design [feature]` |
| `DESIGN_DOC_INVALID` | 设计文档缺少标题或主要章节结构 | 设计文档结构不完整 | 按模板补齐章节后重试 |
| `REQUIREMENT_SOURCE_MISSING` | 无法定位任何关联的用户故事、PRD 或技术预研 | 未找到可追溯的需求来源 | 在设计文档中补充引用后重试 |
| `REPORT_WRITE_FAILED` | 质量报告写入失败 | 无法写入检查报告 | 检查 `.ai/quality/` 目录权限后重试 |

## 示例

```bash
/t-design-check <feature>
```

输出：
```text
总分: 91/100 (优秀，可进入后续拆解)

需求追溯性: 19/20 (-1: 缺少一个用户故事来源)
现有实现分析准确性: 15/15
API 设计完整性: 18/20 (-2: 缺少 409 错误响应说明)
数据库设计完整性: 20/20
前端设计完整性: 9/10 (-1: 空态说明不足)
测试与验收策略: 10/10
决策闭合与文档规范: 5/5

P1 问题:
- `4.2 API 接口设计` 缺少冲突场景错误响应说明

修复步骤:
- 在关键写接口下补充 409/422 等业务错误响应
```

## 质量门禁
- 分项分值之和必须等于 100。
- 每个扣分项必须有文件定位。
- 结论必须可追溯到证据。
- `needs_user_answer=0`，决策闭合扫描通过。
- 影响设计的 Active Decision 均有 Decision Trace。
- 质量结论只约束本次检查报告；是否跳过修复继续 `/t-task` 由用户按风险决定。
