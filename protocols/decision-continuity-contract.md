# Decision Continuity Contract

本协议定义 feature 在 Decision、PRD、Tech Research、Design、Task 之间的决策持久化、用户决策暴露和下游消费规则。

## Runtime Artifact

- 决策账本：`.ai/decision-log/<feature>.md`
- Decision Brief 仍负责立项、Scope Direction 和初始 D0/D1 决策。
- 决策账本负责整个 feature 生命周期中已确认决策、已解决问题和显式延期问题的连续性。
- PRD、Tech Research、Design 和 Task 保留自身领域事实；账本只保存足以避免重复提问和追踪覆盖关系的决策摘要，不复制整份上游文档。

旧 feature 没有决策账本时，首个读取到现有 Decision Brief、PRD 或 Tech Research 的阶段必须从其中已确认决策初始化账本。不得把 Open Questions、假设或风险自动升级为已确认决策。

## Stable IDs

- 决策 ID：`DEC-<feature>-NNN`
- 问题 ID：`Q-<feature>-NNN`
- ID 一经被下游引用不得复用或改名。
- 已确认决策发生变化时创建新 DEC，并用 `Supersedes` 指向旧 DEC；旧记录保留并标记 `Superseded`。

## Required Structure

```markdown
# <feature> Decision Log

## Active Decisions

| ID | Level | Topic | Decision | Rationale | Decided By | Source | Affects | Reopen When | Supersedes |
|---|---|---|---|---|---|---|---|---|---|
| DEC-...-001 | D0/D1/D2 | stable.topic.key | ... | ... | user/agent/repository-fact | path#section | prd/design/task/test | ... / — | — |

## Resolved Questions

| ID | Topic | Resolution | Decision ID | Source |
|---|---|---|---|---|
| Q-...-001 | stable.topic.key | ... | DEC-...-001 | conversation / path#section |

## Deferred Questions

| ID | Topic | Why Non-blocking Now | Owner Stage | Must Resolve Before | User Informed |
|---|---|---|---|---|---|
| Q-...-002 | stable.topic.key | ... | t-design | t-task | yes |

## Superseded Decisions

| ID | Superseded By | Previous Decision | Source |
|---|---|---|---|
```

`Topic` 使用稳定、可检索的语义键，例如 `retention.failed-payment`、`scope.mobile-client`。同一语义问题即使措辞不同也复用同一 Topic。

## Decision Exposure Gate

任何阶段在写入或交付产物前，必须先把不确定项分成以下四类：

| 类型 | 判定 | 必须动作 |
|---|---|---|
| `fact_lookup` | 可从仓库、既有文档或外部权威来源查明 | 先调查，不询问用户，不写成待确认 |
| `agent_decision` | D2 工程取舍，且不改变产品语义、风险接受、显著成本或兼容承诺 | agent 明确选择，记录 DEC、依据和影响 |
| `needs_user_answer` | 影响目标、范围、业务规则、权限/安全边界、显著成本、兼容性、用户流程、验收目标或风险接受 | 先查账本；未解决时立即使用 `AskUserQuestion`，回答前停止写入或交付 |
| `verification_action` | 当前方向已确定，只缺不需要用户选择的外部证据 | 记录验证对象、负责人、完成条件和失败影响，不写成待确认决策 |

完成态不变量：

- PRD、Tech Research、Design 和 Task 中 `needs_user_answer` 必须为 `0`。
- `Deferred Questions` 只允许保存确实不影响当前产物、已指定 owner stage 和最迟解决阶段的问题。
- 写入延期问题前必须在本轮响应中明确告知用户；`User Informed` 只能在告知后写 `yes`。
- 到达 `Must Resolve Before` 对应阶段时，延期问题自动变为 `needs_user_answer`。
- 不能因为文档状态是 `Draft` 就把用户决策静默写入正文。

## Before Asking

任何 `AskUserQuestion` 前必须：

1. 读取 `.ai/decision-log/<feature>.md`、相关 Decision Brief 和当前上游产物。
2. 按 Topic 检查 Active Decisions、Resolved Questions 和 Deferred Questions。
3. 已解决时直接采用，不重复询问。
4. 只有出现新冲突证据或满足原决定的重开条件时才重新提问；问题中必须引用旧 DEC、冲突证据和被阻塞动作。
5. 用户回答后，先写入或更新 Decision Log，再更新拥有该事实的 PRD、Tech Research 或 Design。

## Artifact Trace

PRD、Tech Research、Design 和 Task 必须包含或在其现有决策章节中提供以下追踪关系：

| Decision ID | Applied / Not Applicable / Superseded | Artifact Location | Notes |
|---|---|---|---|

- 所有对当前阶段有影响的 Active Decision 必须逐项标记。
- `Not Applicable` 必须说明原因。
- 不得引用 Superseded Decision 作为当前依据。
- 新增的 D1/D2 决策必须回写账本；D0/D1 产品决策由用户确认，D2 仅在不改变产品语义、风险接受、显著成本或兼容承诺时可由 agent 决定。

## Closure Scan

生成阶段在交付 PRD、Tech Research 或 Design 前，必须运行：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py <artifact-path>
```

扫描结果只是候选未决表达，不代替语义分类：

- 命中用户决策 → 标记 `needs_user_answer`，提问并停止。
- 命中 agent 授权范围内的 D2 → 作出决定并记录依据。
- 命中事实缺口 → 调查。
- 命中外部验证 → 改写为明确验证动作。
- 只有重新扫描通过后才可交付产物。
