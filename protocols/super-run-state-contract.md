# Super Run State And Execution Contract

本协议定义 `/t-super-run` 的目标级计划、持久化状态、主会话执行顺序和 Goal 闭环。单一主会话按 task 切换角色规范，通过状态文件保存检查点，不调用 subagent。

super-run 状态与 `${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md` 相互独立，不得互相迁移、覆盖或推导。

## Runtime Artifacts

```text
.ai/super-run/<feature>/
├── .state.json
├── backend.md
├── frontend.md
└── demo.md
```

- `.state.json` 是 super-run 状态的唯一事实源。
- `<phase>.md` 是当前 phase 的目标级计划，不生成 slot manifest、item 目录或 item 文件。
- 只创建 active phase 对应的计划文件。

## Supported Phases And Tasks

`supported_phases` 固定为 `backend | frontend | demo`，默认顺序为 `backend -> frontend -> demo`。

| phase | task 顺序 | agent 规范 |
| --- | --- | --- |
| backend | `dev -> test -> accept` | `backend-dev -> backend-test -> backend-accept` |
| frontend | `dev -> test -> accept` | `frontend-dev -> frontend-test -> frontend-accept` |
| demo | `dev -> accept` | `demo-dev -> demo-accept` |

`active_phases` 只包含设计、PRD 或明确用户要求中的真实交付端。显式传入的 phase 不适用时终止，不得为满足命令而编造交付范围。

`phases` 只包含 active phase。`current_phase` 执行时指向当前 phase；当前 phase 完成后切换到下一个未完成 active phase，全部完成时写为 `null`。

未传 `--phase` 时：

1. 首次运行从设计与需求来源识别 `active_phases`。
2. 已有状态时按默认顺序选择首个不是 `completed | skipped` 的 active phase。
3. 所有 active phase 均完成时返回已完成，不创建新 Goal。

## State Shape

```json
{
  "feature": "sample-feature",
  "current_phase": "backend",
  "active_phases": ["backend", "frontend", "demo"],
  "phases": {
    "backend": {
      "status": "in_progress",
      "plan": ".ai/super-run/sample-feature/backend.md",
      "tasks": {
        "dev": {
          "status": "completed",
          "agent_spec": "${CLAUDE_PLUGIN_ROOT}/agents/backend-dev.md",
          "references": [
            "${CLAUDE_PLUGIN_ROOT}/guides/backend/index.md"
          ],
          "evidence": ["backend/src/..."]
        },
        "test": {
          "status": "in_progress",
          "agent_spec": "${CLAUDE_PLUGIN_ROOT}/agents/backend-test.md",
          "references": [
            "${CLAUDE_PLUGIN_ROOT}/guides/backend/testing.md",
            "${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md"
          ],
          "evidence": []
        },
        "accept": {
          "status": "pending",
          "agent_spec": "${CLAUDE_PLUGIN_ROOT}/agents/backend-accept.md",
          "references": [],
          "evidence": []
        }
      }
    }
  },
  "sources": {
    "design": ".ai/design/sample-feature.md",
    "requirements": [],
    "decisions": [],
    "research": []
  }
}
```

Task 必填字段：

- `status`
- `agent_spec`
- `references`
- `evidence`

失败或阻塞时增加 `last_error`。`.state.json` 不记录时间类元数据。

## Status Rules

状态只允许：

- `pending`：尚未执行。
- `in_progress`：已开始且尚未得到完成证据。
- `failed`：当前尝试失败，但可由执行闭环继续修复。
- `blocked`：需要用户决策、权限、外部系统变化或其他当前无法自行解决的条件。
- `completed`：交付物与当前 task 的验证均完成。
- `skipped`：已有证据证明 task 或 phase 不适用。

Phase 聚合顺序：

1. 任一 task 为 `blocked`，phase 为 `blocked`。
2. 否则任一 task 为 `failed`，phase 为 `failed`。
3. 全部 task 为 `skipped`，phase 为 `skipped`。
4. 全部 task 为 `completed | skipped` 且至少一个为 `completed`，phase 为 `completed`。
5. 任一 task 为 `in_progress | completed`，phase 为 `in_progress`。
6. 其他情况为 `pending`。

执行 task 前先写 `in_progress`。成功后写 `completed`、删除旧 `last_error`，并追加文件、命令、报告或日志证据；失败后先写 `failed` 和 `last_error`，再决定自动修复或转为 `blocked`。状态写入失败时重试一次，仍失败则停止，避免继续产生无法恢复的修改。

恢复 `in_progress` task 时，先检查工作区、已有交付物和验证证据，再从未满足的完成条件继续；不得把中断状态直接视为成功，也不得无条件重复可能产生副作用的动作。

## Phase Plan Contract

`<phase>.md` 只包含：

- phase 目标、范围和完成条件。
- Source Trace：本轮实际读取的设计、PRD、用户故事、Decision Brief、Decision Log、技术预研和项目事实。
- Decision Trace：影响当前 phase 的 Active Decision 及应用位置。
- task 表：`task | goal | agent spec | related documents | deliverable | validation`。
- 必要的恢复说明和上游 handoff。

每个 task 固定为一个目标级责任闭环，不继续拆 item。`related documents` 必须列出执行前要读取的真实路径，包括 agent 规范中的 Read Order 和本 feature 相关文档；不得只写“按需阅读相关指南”。

计划采用 outcome-first 结构：明确当前层级、完成条件、约束、工具/证据入口和停止规则，不预先规定可从仓库事实判断的逐步操作。阶段切换时记录简短 handoff；例行工具调用不写成长篇过程日志。

已有计划恢复执行时重新读取上游来源。若来源变化影响未执行 task，更新计划与状态；若变化使已完成工作失效，重新打开受影响 task 及其下游 test/accept，并在计划中记录原因。

## Main-Session Role Loading

`/t-super-run` 不调用 `Agent` 或其他 subagent 调度工具。每个 task 开始前，主会话必须：

1. 读取 `agent_spec` 全文，把它作为当前 task 的角色边界。
2. 按 agent 规范的 Read Order 读取计划列出的关联文档。
3. 只加载当前 task 所需的 feature 上下文，不预读后续角色的全部 guide。
4. 完成 task 后把状态、证据、剩余风险和 handoff 写入运行时产物，再切换角色。

Agent 规范在这里是主会话执行指南，不适用 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 的 prompt 注入步骤。

## Test And Acceptance Loop

- backend/test 先按 `backend-test` 规范编写或维护场景测试并做编译验证，再由主会话按 `${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md` 执行定向测试与失败分类。
- frontend/test 按 `frontend-test` 规范完成测试资产和定向执行。
- 测试发现生产代码缺陷时，在同一个 test task 内读取对应 dev agent 规范后修复，再重新执行受影响测试；不得弱化断言、权限预期或业务规则。
- demo/dev 同时承担 Demo/E2E 资产维护和定向执行，demo 不新增独立 test task。Demo 失败时读取 `demo-diagnose` 规范分类；测试资产问题仍在 demo/dev 修复，backend/frontend 实现问题则在同一 task 内切换到对应 dev 规范修复，并补跑底层定向测试和 Demo。
- accept 必须保持对应 accept agent 的只读验收边界；允许写验收报告，不得直接修改生产代码或测试来制造通过结果。
- accept 拒绝时按证据重新打开 dev 或 test，并把 accept 重置为 `pending`。修复、重测后重新验收，直到通过或进入 `blocked`。

## Goal Contract

计划和初始状态成功写入后，主动调用运行时 `/goal` 或等价原生 Goal API。目标必须包含：

- outcome：完成 `<feature>/<phase>` 计划。
- constraints：不调用 subagent；持续更新 `.state.json`；遵守计划中的 agent 规范和来源边界。
- verification：全部 task 为 `completed | skipped`，必要测试通过，accept 给出允许进入下游的结论。

推荐目标：

```text
完成 <feature> 的 <phase> phase。以 .ai/super-run/<feature>/<phase>.md 为计划，
以 .ai/super-run/<feature>/.state.json 为状态真相；不调用 subagent，按当前 task
列出的 agent 规范直接执行、验证并记录证据。仅当全部 task 完成或跳过且 accept
通过时结束；需要用户决策或外部条件时记录 blocked 并暂停。
```

- 已存在同一 feature/phase 的 Goal 时复用或恢复，不重复创建。
- 存在无关的活动 Goal 时不得静默覆盖；停止并请用户先编辑、完成或清除现有 Goal。
- Goal 只在 phase 聚合为 `completed | skipped` 后完成。accept 的 `ACCEPTED`，或没有 P0/P1 的 `ACCEPTED_WITH_IMPROVEMENTS`，可作为通过结论。
- `blocked` 不等于完成；保留状态并等待用户或外部条件后恢复。

## Failure Rules

- 设计文档缺失：终止并提示先运行 `/t-design <feature>`。
- 状态 JSON 损坏或结构非法：停止并报告具体字段，不覆盖原文件。
- 需求来源或 Active Decision 冲突：写入 `blocked`，按 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md` 处理。
- 验证命令不存在：先从目标项目配置和脚本查明真实入口；无法查明时标记 `blocked`，不得编造命令。
- 自动修复连续三次得到相同失败且没有新证据：保留失败证据并转为 `blocked`，不要用无界重试掩盖阻塞。
