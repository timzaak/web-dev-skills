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
设计生成状态统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/design-state-contract.md`

## 目标
- 评估技术设计文档的可实施性、完整性与一致性。
- 给出可复查的 100 分量化结果。
- 输出 P0/P1/P2 修复清单。
- 给出明确的设计质量检查结论；本检查为可选，不作为 `/t-task` 的硬性前置。
- 发现必须由用户裁决的设计问题时，使用 `AskUserQuestion` 阻塞式提问，不得只写入问题清单后继续。

评分维度、严重级别和报告要求统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/design-check-rubric.md`

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
- 对主文档和全部适用分端文档运行 `check-decision-closure.py`，对命中项按 Decision Exposure Gate 分类。
- 运行 `python ${CLAUDE_PLUGIN_ROOT}/scripts/check-design.py ".ai/design/[feature].md" --require-complete`；失败时先按结构化结果修正文档，不进入评分。
- 核对 Decision Trace 是否覆盖所有影响设计的 Active Decision，且没有使用 Superseded Decision；分端文档的 DEC 子集不得与主文档矛盾。
- 核对设计文档与需求来源的一致性。
- 若设计引用 `.ai/user-stories`，确认其为 draft 候选来源且路径存在；若同时存在相关 `docs/user-stories`，检查是否存在未说明冲突。
- 如果设计文档声明为纯技术方案且不涉及业务逻辑变动，可接受 `.ai/tech-research/[feature].md` 作为唯一需求来源；此时不得因缺少 PRD/用户故事扣 P0，但需要核对技术目标、约束、影响范围和风险是否一致。
- 核对设计文档与项目规范的一致性。
- 按 `${CLAUDE_PLUGIN_ROOT}/protocols/design-check-rubric.md` 分别检查：主文档（需求追溯、跨端契约与汇总）、backend 分端（API、数据库、领域逻辑）、frontend 分端（页面、状态与数据流）、flutter 分端（分层、状态管理、导航）与测试策略。
- 核对跨端一致性：`frontend.md` / `flutter.md` 的 API 依赖与契约源（`backend.md` 或现有接口）不冲突；主文档 §8 是否全量汇总各端文件影响范围。
- 评估设计方案的章节组织是否内聚：若同一业务闭环、同一数据模型或同一外部契约被拆分为多个独立章节，应在设计阶段合并，避免 `/t-task` 产出颗粒度过细的 item；分端文档内部不得重复其他端的设计内容。
- 若发现 `${CLAUDE_PLUGIN_ROOT}/protocols/design-check-rubric.md` 定义的 `needs_user_answer`，先查 Decision Log；未解决时立即使用 `AskUserQuestion` 向用户提问。回答前不生成通过结论；回答后先更新 Decision Log 和设计文档、重新运行决策闭合扫描，再继续评分。
- 按适用维度归一化生成评分与问题清单。
- 严格按 rubric 的 Pass Gate 输出 `PASS / CONDITIONAL PASS / FAIL`，不得只凭总分宣布通过。
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

## 示例

```bash
/t-design-check <feature>
```

输出：
```text
总分: 91/100 (优秀，可进入后续拆解)
计分维度: 需求追溯性、现有实现分析、后端设计、前端设计、测试与验收、决策闭合与跨端一致性

需求追溯性: 19/20 (-1: 缺少一个用户故事来源)
现有实现分析准确性: 15/15
后端设计完整性: 22/25 (-2: 缺少 409 错误响应说明; -1: 幂等说明缺失)
前端设计完整性: 14/15 (-1: 空态说明不足)
测试与验收策略: 10/10
决策闭合与跨端一致性: 10/10

P1 问题:
- `backend.md §4.2 API 接口设计` 缺少冲突场景错误响应说明

修复步骤:
- 在 backend.md 关键写接口下补充 409/422 等业务错误响应
```

## 质量门禁
- 总分按 `${CLAUDE_PLUGIN_ROOT}/protocols/design-check-rubric.md` 的适用维度归一化为 100 分制，报告列出参与计分的维度。
- 每个扣分项必须有文件定位（主文档或具体分端文档）。
- 结论必须可追溯到证据。
- `needs_user_answer=0`，主文档与全部分端文档决策闭合扫描通过。
- `check-design.py` 通过，结论符合 rubric 的 Pass Gate。
- 影响设计的 Active Decision 均在主文档 Decision Trace 中有结论。
- 质量结论只约束本次检查报告；是否跳过修复继续 `/t-task` 由用户按风险决定。
