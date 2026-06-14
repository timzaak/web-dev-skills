# [功能名称] Decision Brief

**生成时间**: [自动生成时间戳]
**状态**: Draft
**输入来源**: [用户需求 / 现有文档 / 当前对话]

## 1. Verdict

- **结论**: [Proceed / Research First / Needs Clarification / Park / Reject]
- **信心**: [High / Medium / Low]
- **Scope Direction**: [Expand / Selective Expand / Hold / Reduce / Explore]
- **推荐下一步**: [`/t-tech-research <feature>` / `/t-prd <feature>` / 重跑 `/t-decision <feature>` / 停止]
- **理由**: [一句话]

## 2. Problem

- **真实问题**: [一句话，不写方案]
- **不做的后果**: [用户、业务或工程损失]
- **代理问题检查**: [是否在解决真实问题；如不是，写更直接的问题]

## 3. Target User

- **目标用户**: [角色 + 场景 + 后果]
- **现状替代方案**: [现在怎么解决]
- **痛点成本**: [时间 / 金钱 / 风险 / 体验 / 业务阻塞]

## 4. Evidence

| 证据 | 强度 | 说明 |
|---|---|---|
| [行为/付费/反馈/文档/代码事实] | Strong / Medium / Weak | [支持或反对继续做的原因] |

## 5. Scope Direction

- **In Scope**:
  - [进入后续流程的范围]
- **Not in Scope**:
  - [明确不做的范围]
- **Possible Expansions**:
  - [可选增强项；未确认不进入 scope]

## 6. Options Considered

| 方案 | 类型 | 收益 | 成本/风险 | 结论 |
|---|---|---|---|---|
| [方案 A] | Minimal / Recommended / Ambitious / Reject | [收益] | [成本/风险] | [选择或排除原因] |

## 7. Product Decisions

| Level | 决策项 | 结论 | 依据 | 影响 |
|---|---|---|---|---|
| D0 | [CEO/Product 决策] | [结论] | [依据] | [影响] |
| D1 | [产品执行决策] | [结论] | [依据] | [影响] |

## 8. Risks

| 风险项 | 等级 | 缓解或后续动作 |
|---|---|---|
| [风险] | P0/P1/P2 | [动作] |

## 9. Open Questions

| 问题 | 是否阻塞 PRD | 需要谁决策 | 建议动作 |
|---|---|---|---|
| [问题；无则写“无”] | 是/否 | [负责人] | [动作] |

## 10. Handoff

- **给 `/t-tech-research`**: [技术未知项、依赖、成本或风险]
- **给 `/t-prd`**: [目标用户、范围、成功标准、已确认决策]
- **给 `/t-design`**: [不得静默改变的边界、scope、风险]
