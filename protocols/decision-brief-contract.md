# Decision Brief Contract

Decision Brief 是 `/t-decision` 的输出，位于 PRD 之前，用来决定 feature 是否进入后续流程。

## Files

- Source: `.ai/decision/<feature>.md`
- Preview: `.ai/preview/decision/<feature>.html`

Preview 必须遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/html-show-contract.md`。

## Verdict

| Verdict | 含义 | 下一步 |
|---|---|---|
| `Proceed` | 产品方向明确，值得继续 | `/t-prd` 或 `/t-tech-research` |
| `Research First` | 值得探索，但技术可行性/成本/依赖会影响范围 | `/t-tech-research` |
| `Needs Clarification` | 关键产品判断缺失 | 补齐后重跑 `/t-decision` |
| `Park` | 暂存，不进入当前实现链路 | 记录重启条件 |
| `Reject` | 不建议做 | 停止 |

## Required Sections

- `## 1. Verdict`
- `## 2. Problem`
- `## 3. Target User`
- `## 4. Evidence`
- `## 5. Scope Direction`
- `## 6. Options Considered`
- `## 7. Product Decisions`
- `## 8. Risks`
- `## 9. Open Questions`
- `## 10. Handoff`

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

## Downstream

- `/t-tech-research` 承接技术未知项，不改写 Verdict。
- `/t-prd` 承接目标用户、范围、成功标准和已确认 D0/D1；不得把 Open Questions 写成已确认。
- `/t-prd-check` 检查 PRD 是否偏离 Decision Brief。
- `/t-design` 不得用技术方案推翻 Decision Brief；冲突时回到 `/t-decision`。
