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

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（判断产物写入位置或脚本入口与插件默认冲突时读）
需求来源边界：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`（区分草稿与已发布需求来源或处理两者冲突时读）
决策连续性和用户决策暴露：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`（提问、更新决策账本或处理决策暴露门禁时读）
设计生成状态：`${CLAUDE_PLUGIN_ROOT}/protocols/design-state-contract.md`（校验设计 .state.json 时读）
评分维度、Clarification Gate、严重级别、报告结构与 Pass Gate：`${CLAUDE_PLUGIN_ROOT}/protocols/design-check-rubric.md`（评分或生成分级结论前读）

本检查为可选，不作为 `/t-task` 的硬性前置；质量结论只约束本次检查报告，是否跳过修复继续 `/t-task` 由用户按风险决定。

## 输入范围

- 设计主文档：`.ai/design/[feature].md`
- 分端设计文档（适用端必须存在）：`.ai/design/[feature]/backend.md`、`.ai/design/[feature]/frontend.md`、`.ai/design/[feature]/flutter.md`
- 设计生成状态：`.ai/design/[feature]/.state.json`（存在时必须为 `complete`）
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

- 校验主文档是否存在，并按主文档 §4.2 交付端范围校验适用端的分端文档是否存在。
- `.ai/design/[feature]/.state.json` 存在但状态不是 `complete` 时停止，提示先恢复 `/t-design [feature]`。
- 从设计文档提取引用的用户故事、PRD、技术预研、接口、数据库变更、各端范围、测试策略。
- 运行 `python ${CLAUDE_PLUGIN_ROOT}/scripts/check-design.py ".ai/design/[feature].md" --require-complete`；失败时先按结构化结果修正文档，不进入评分。
- 对主文档和全部适用分端文档运行决策闭合扫描；`needs_user_answer` 和澄清处理按 rubric 的 Clarification Gate 执行（先查 Decision Log，未解决时 `AskUserQuestion` 阻塞提问，回答后更新 Decision Log 和设计文档再重新扫描）。
- 核对设计文档与需求来源的一致性。设计引用 `.ai/user-stories` 时确认其为 draft 候选来源且路径存在；同时存在相关 `docs/user-stories` 时检查是否有未说明冲突。纯技术方案可接受 `.ai/tech-research/[feature].md` 作为唯一需求来源，不得因缺少 PRD/用户故事扣 P0。
- 核对设计文档与项目规范的一致性。
- 按 rubric 的维度和 Detailed Checks 分别检查：主文档（需求追溯、跨端契约与汇总）、backend 分端（API、数据库、领域逻辑）、frontend 分端（页面、状态与数据流）、flutter 分端（分层、状态管理、导航）与测试策略。
- 评估设计方案的章节组织是否内聚：若同一业务闭环、同一数据模型或同一外部契约被拆分为多个独立章节，应在设计阶段合并，避免 `/t-task` 产出颗粒度过细的 item；分端文档内部不得重复其他端的设计内容。
- 按 rubric 的归一化规则生成评分与问题清单，并按其 Pass Gate 输出 `PASS / CONDITIONAL PASS / FAIL`，不得只凭总分宣布通过。
- 输出下一步建议：通过或风险可接受时进入 `/t-task [feature]`；修复后可重新运行 `/t-design-check [feature]`。
- 写入报告：`.ai/quality/design-check-[feature]-[YYYYMMDD-HHMMSS].md`。

## 错误处理

| 错误码 | 触发条件 | 用户可见提示 | 恢复动作 |
|---|---|---|---|
| `DESIGN_DOC_MISSING` | 设计主文档不存在 | 未找到设计主文档 | 先运行 `/t-design [feature]` |
| `DESIGN_STACK_DOC_MISSING` | 主文档 §4.2 标记适用，但对应分端文档不存在 | 未找到适用端的分端设计文档 | 重新运行 `/t-design [feature]` 补齐该端 |
| `DESIGN_DOC_INVALID` | 设计文档缺少标题或主要章节结构 | 设计文档结构不完整 | 按模板补齐章节后重试 |
| `DESIGN_GENERATION_INCOMPLETE` | `.state.json` 存在且不是 `complete` | 设计仍在生成或上一轮失败 | 恢复或重新运行 `/t-design [feature]` |
| `REQUIREMENT_SOURCE_MISSING` | 无法定位任何关联的用户故事、PRD 或技术预研 | 未找到可追溯的需求来源 | 在设计文档中补充引用后重试 |
| `REPORT_WRITE_FAILED` | 质量报告写入失败 | 无法写入检查报告 | 检查 `.ai/quality/` 目录权限后重试 |

## 质量门禁

- 每个扣分项必须有文件定位（主文档或具体分端文档）。
- 其余门禁（`needs_user_answer=0`、决策闭合扫描、`check-design.py`、Decision Trace 覆盖、Pass Gate）以 rubric 为准。
