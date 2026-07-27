# Decision Brief Contract

Decision Brief 是 `/t-decision` 的输出，位于 PRD 之前，用来决定 feature 是否进入后续流程。

## Files

- Source: `.ai/decision/<feature>.md`
- Cross-stage decision log: `.ai/decision-log/<feature>.md`

## Verdict

| Verdict | 含义 | 下一步 |
|---|---|---|
| `Proceed` | 产品方向明确，值得继续 | 按主要未知项选择 `/t-prd` 或 `/t-tech-research` |
| `Research First` | 值得探索，但技术可行性/成本/依赖会影响范围 | `/t-tech-research` |
| `Needs Clarification` | 关键产品判断缺失 | 补齐后重跑 `/t-decision` |
| `Park` | 暂存，不进入当前实现链路 | 记录重启条件 |
| `Reject` | 不建议做 | 停止 |

## Required Sections

- `## 1. Verdict`
- `## 2. Problem`
- `## 3. Target User`
- `## 4. Evidence`
- `## 5. Lethal Assumptions & Kill Criteria`
- `## 6. Scope Direction`
- `## 7. Options Considered`
- `## 8. Product Decisions`
- `## 9. Risks`
- `## 10. Open Questions`
- `## 11. Handoff`

## 六问诘问 Spine

`/t-decision` 的诘问主线是六问 forcing questions，写 Verdict 前必须逐项有结论或显式跳过理由。六问跑完后才进入场景追问框架（Product / Internal / Engineering Enabler / Builder），框架只补充场景特有判断，不重复六问。

1. 谁在痛、痛到什么程度（强制量化）。
2. 这是问题，还是方案（至少提一个 reframe 替代定义）。
3. 用户现在怎么绕（现状替代方案与摩擦成本）。
4. 最小楔子是什么（wedge vs MVP）。
5. 哪个假设错了会致命（最小证伪方式 + Kill Criteria）。
6. 有没有更大、更易讲、更高杠杆的版本（10x 反转）。

## Scope Direction

只允许：

- `Expand`
- `Selective Expand`
- `Hold`
- `Reduce`
- `Explore`

后续 skill 不得静默改变已确认 scope。

## Decision Levels

| Level | 含义 | 处理方式 |
|---|---|---|
| `D0` | CEO/Product 决策：目标用户、商业承诺、优先级、合规/安全/权限、兼容性、显著成本、是否继续 | 必须确认并记录 |
| `D1` | 产品执行决策：默认流程、关键异常、可见性、验收优先级 | 影响 PRD 时记录 |
| `D2` | 工程决策：实现方式、测试组织、内部重构 | 不进入 Decision Brief |

Product Decisions 必须分配 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md` 定义的稳定 DEC ID，并同步进入 Decision Log。Open Questions 必须分配 Q ID；未确认问题不得写入 Active Decisions。

## Downstream

- `/t-prd` 与 `/t-tech-research` 没有全局固定顺序：技术未知会改变产品范围时先预研，产品边界决定技术选择时先写 PRD 草稿。
- `/t-tech-research` 承接技术未知项，不改写 Verdict。若 Verdict=Research First 且 Decision Brief 含致命假设，可被指派“最小证伪计划”作为预研目标。
- `/t-prd` 承接目标用户、范围、成功标准和已确认 D0/D1；不得把 Open Questions 写成已确认。
- PRD 草稿后的预研若发现需要改变范围、业务规则、用户流程或验收目标，必须回到 `/t-prd` 更新草稿；进入 `/t-design` 前，PRD 与技术预研不得存在未解释冲突。
- `/t-prd-check` 检查 PRD 是否偏离 Decision Brief。
- `/t-design` 不得用技术方案推翻 Decision Brief；冲突时回到 `/t-decision`。
- `Park` / `Reject` 必须引用 §5 的 Kill Criteria 作为依据。
