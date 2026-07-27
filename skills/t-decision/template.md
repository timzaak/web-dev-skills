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
- **量化痛点**: [频率 / 时长 / 人数 / 金钱 / 业务阻塞强度；给不出则写“待量化”+ 原因]
- **不做的后果**: [用户、业务或工程损失]
- **替代问题定义 / Reframe**: [六问第 2 问提出的替代问题定义；记录用户最终确认的真问题]

## 3. Target User

- **目标用户**: [角色 + 场景 + 后果]
- **现状替代方案**: [现在怎么解决；六问第 3 问]
- **现状摩擦成本**: [绕法耗费的时间 / 钱 / 风险 / 人工协调]
- **痛点成本**: [时间 / 金钱 / 风险 / 体验 / 业务阻塞]

## 4. Evidence

| 证据 | 强度 | 说明 |
|---|---|---|
| [行为/付费/反馈/文档/代码事实] | Strong / Medium / Weak | [支持或反对继续做的原因] |

## 5. Lethal Assumptions & Kill Criteria

来自六问第 5 问。列出 1-3 个核心假设，标出致命项，给出最小证伪方式和放弃条件。

| 假设 | 是否致命 | 最小证伪方式 | 成本 | Kill Criteria |
|---|---|---|---|---|
| [核心假设] | 是/否 | [如何用最小成本验证] | [时间/钱/人力] | [什么结果会让你直接放弃] |

## 6. Scope Direction

- **In Scope**:
  - [进入后续流程的范围]
- **Not in Scope**:
  - [明确不做的范围]
- **Possible Expansions**:
  - [可选增强项；未确认不进入 scope]

## 7. Options Considered

| 方案 | 类型 | 收益 | 成本/风险 | 结论 |
|---|---|---|---|---|
| [方案 A] | Wedge / Minimal / Recommended / Ambitious / 10x / Reject | [收益] | [成本/风险] | [选择或排除原因] |

类型说明：`Wedge` 最薄学习切片（验证致命假设）；`Minimal` 最小可验证价值；`Recommended` 当前证据下最合理；`Ambitious`/`10x` 更大或更高杠杆版本（来自六问第 6 问）。

## 8. Product Decisions

| Decision ID | Level | Topic | 决策项 | 结论 | 依据 | 影响 |
|---|---|---|---|---|---|---|
| `DEC-[feature]-001` | D0 | [stable.topic.key] | [CEO/Product 决策] | [结论] | [依据] | [影响] |
| `DEC-[feature]-002` | D1 | [stable.topic.key] | [产品执行决策] | [结论] | [依据] | [影响] |

## 9. Risks

| 风险项 | 等级 | 缓解或后续动作 |
|---|---|---|
| [风险] | P0/P1/P2 | [动作] |

## 10. Open Questions

| 问题 | 是否阻塞 PRD | 需要谁决策 | 建议动作 |
|---|---|---|---|
| [问题；无则写“无”] | 是/否 | [负责人] | [动作] |

## 11. Handoff

- **给 `/t-tech-research`**: [技术未知项、依赖、成本或风险；若 Verdict=Research First 且有致命假设，写明最小证伪计划]
- **给 `/t-prd`**: [目标用户、范围、成功标准、已确认决策]
- **给 `/t-design`**: [不得静默改变的边界、scope、风险]
