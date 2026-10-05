# Super Run All Pipeline Contract

`t-super-run-all` 的跨 phase 接力、每阶段质量链与 pipeline 游标的单一事实源。

phase 内的计划、状态、执行与验收以 `${CLAUDE_PLUGIN_ROOT}/protocols/super-run-state-contract.md` 为准；phase 启用与默认顺序以 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 为准。本契约只定义跨 phase 接力和质量链，不重复它们的内容。

## Pipeline 范围

- 输入为设计已 `complete` 的 feature；连跑范围取 `.ai/super-run/<feature>/.state.json` 的 `active_phases`。
- 每个按规范顺序选出的 phase 依次执行：super-run phase 闭环 → `review(--fix)` → `simplify` → `push`；全部通过后进入下一个 phase。质量链修复后的证据失效、回归和重新验收按下文的 Push 前门禁执行，不能沿用修改前的 accept 结论。
- 质量链步骤是 `t-super-run-all` 的内部步骤，按各自契约执行，不构成对独立 `t-*` 命令的自动触发；用户的一次手工调用即授权整条链。
- pipeline 以 `push` 收口。`t-prd-publish` 与 `t-release` 不在链内，仍由用户手工触发。

## Phase 顺序

pipeline 顺序是 [task-phase-execution.md](${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md) 默认顺序的固定投影：

```text
backend -> frontend -> extension -> miniapp -> flutter -> web-demo -> extension-demo -> flutter-demo
```

只取 `active_phases` 命中的项。聚合为 `skipped` 的 phase 不进入质量链，直接视为已处理。

## Pipeline 游标

`.ai/super-run/<feature>/.pipeline.json` 只记录质量链进度；phase 完成真相在 `.state.json`，两者不得互相推导或覆盖。`t-super-run` 不读取该文件。

```json
{
  "feature": "sample-feature",
  "chain": ["review", "simplify", "push"],
  "phases": {
    "backend": {
      "input_fingerprint": "sha256:<64 位十六进制摘要>",
      "review": {"status": "completed"},
      "simplify": {"status": "in_progress", "failures_without_progress": 0},
      "push": {"status": "pending", "last_error": null, "ci_session": "backend-push-1"}
    }
  }
}
```

- `chain` 固定为 `["review", "simplify", "push"]`，不允许跳过或重排。
- step 状态只允许 `pending | in_progress | failed | blocked | completed`。
- 失败时记录 `last_error`；`failures_without_progress` 持久化在当前 step，实质进展后才能清零，同一失败连续三次无新证据转 `blocked`。
- 不记录时间类元数据。
- 游标只由 `t-super-run-all` 创建和更新；损坏或结构非法时停止并保留原文件，不自动重建。
- `feature` 必须与请求目录及 `.state.json` 一致；只允许 active phase 条目。脚本按 super-run 状态契约校验 phase/task 必填字段、状态聚合与 accept 门禁；非法输入返回结构化 `error`，不把缺字段或不一致状态视为未规划。
- 每个 phase 的 `input_fingerprint` 由 `super-run-next.py` 对 `.state.json` 的 `sources` 和当前 phase 记录（含共享状态契约的 `validation_revision`）进行确定性 SHA-256 计算，并随动作返回；它绑定已验收输入，不替代代码和环境证据的适用性核对。重开 task 时依共享契约递增 revision，不能因报告路径复用而沿用旧绑定。
- 首次 `review` 前创建该 phase 游标并写入返回的指纹。已有游标的指纹缺失或与当前已验收输入不同，脚本返回 `reset_quality`；主会话记录失效原因，将该 phase 全部质量链步骤重置为 `pending` 并绑定新指纹，再重新计算动作。合法旧游标仅缺少绑定时按此规则重新验证，不把历史 `completed` 绑定到新输入。
- phase 重开后先完成必要验证和独立 accept，再绑定新输入；不得提前更新指纹以保留旧质量链结果。受影响的其他已规划 phase 同样重开，其游标在重新验收后失效；无关 phase 保持状态。
- push 的 `ci_session` 在首次执行前持久化，中断、CI 修复及补推时复用；新一轮质量链使用新 session。push 恢复记录和工作区指纹规则见 `${CLAUDE_PLUGIN_ROOT}/protocols/push-execution-contract.md`。

## 质量链步骤

每步开始前写 `in_progress`，结束后写 `completed` 或失败原因：

- **review**：按 `${CLAUDE_PLUGIN_ROOT}/skills/t-review/SKILL.md` 的 `--fix` 模式及 `${CLAUDE_PLUGIN_ROOT}/protocols/review-correctness-contract.md` 完整执行；修复和门禁消费完整发现集（含超过报告摘要上限的发现）。只有无未修复的 CONFIRMED 发现、且无阻塞级未决 PLAUSIBLE 时才可写 `completed`，未决项需要用户裁决时写 `blocked`。
- **simplify**：按 `${CLAUDE_PLUGIN_ROOT}/skills/t-simplify/SKILL.md` 及 `${CLAUDE_PLUGIN_ROOT}/protocols/simplify-cleanup-contract.md` 完整执行，覆盖 review --fix 的修复代码；`NO_CHANGES` 视为完成。
- **push**：按 `${CLAUDE_PLUGIN_ROOT}/skills/t-push/SKILL.md` 执行注释清理和 commit message 总结；按 Push 前门禁先运行 `push.py --check-only`，再带已验收的 `--expected-fingerprint` 提交推送。CI 或 push 失败按该 skill 的失败规则处理；本地 commit 保留时用同一 session 恢复，确认远端包含目标 commit 后才可写 `completed`，工作区干净或脚本没有新建 commit 不能单独证明 push 完成。

## Push 前门禁

每次恢复及计算下一步前，按 super-run 的 Design Source Gate 与 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md` 核对来源和已完成证据；质量链期间也执行此门禁。输入变化时先重开受影响 task 和验收、重新聚合 phase，再计算动作，不能等全部 push 后才核对。

- review 修复、simplify 修改、注释清理、CI 自动修复或主会话 CI 修复后，立即判断证据是否失效；失效时按共享协议重开受影响 task 及 accept，补跑必要行为回归和 Demo 整文件门禁，并串行派发只读 accept。编译、类型检查不能单独替代必要行为回归。
- 即使未改变预期行为，也必须核对相关代码、测试、配置与实际加载产物；机械清理的运行证据复用需有依据，不能默认旧结论继续有效。重新 accept 后由脚本触发 `reset_quality`，从 review 重跑；不得手工保留旧质量链以绕过门禁。
- push 前先完成注释清理并用持久化 session 执行 `push.py --check-only`。CI 修改代码时先执行上述证据失效闭环；最终代码通过必要验证及独立 accept 后，重新执行 check-only 取得稳定工作区指纹，把该值写入 push step 的 `accepted_worktree_fingerprint`。尚需重开 phase 或质量链时停止本次 push 步骤，返回下一步计算。
- 实际提交传入该指纹；脚本发现提交前、CI 后或 commit hook 后代码变化时停止提交或推送，交回验证闭环。恢复已有 commit 时同样核对记录中的代码指纹和推送目标；不能因 CI 通过而跳过 accept。

## 下一步计算

每轮迭代先运行：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/super-run-next.py" "<feature>" --json
```

按返回的 `action` 执行，不得凭内存中的列表推进。`action` 语义：

| action | 含义 |
| --- | --- |
| `plan_first_phase` | 无 super-run 状态；按 super-run 来源加载规则识别 `active_phases` 并规划首个 phase |
| `run_phase` | 执行或恢复指定 phase 的 super-run 闭环 |
| `review` / `simplify` / `push` | 执行指定 phase 的对应质量链步骤 |
| `reset_quality` | 已验收输入变化或合法旧游标未绑定；失效该 phase 的质量链并绑定返回的新指纹 |
| `check_blocked` | 只复核指定 phase/task 或质量步骤的阻塞解除条件，返回 `step=null` 表示 phase 阻塞 |
| `none` | 无可执行动作；`status` 为 `done` 表示全部完成 |
| `none` + `status=blocked` / `status=error` | 停止并报告原因 |

脚本只读状态并计算下一步，不写任何文件。

## 停止条件

只有以下情况停止：

- `check_blocked` 核对后，phase 或质量步骤的阻塞条件仍未解除。
- `super-run-next.py` 返回 `error`（状态或游标损坏、结构非法）。
- demo phase 缺运行环境；按对应 demo 指南补齐后重跑同一命令恢复。
- 全部 phase 与质量链完成。

设计指纹变化按 super-run 共享协议处理（重读设计、重开受影响 task），不额外停车。

## 失败与恢复

- 中断后重跑同一命令：`super-run-next.py` 从磁盘状态重算，已完成的 phase 与质量链步骤不重复执行。
- `check_blocked` 不授权重试：主会话先读取 `last_error`、失败证据和恢复条件；设备、环境、权限或用户裁决等条件已有可复核变化时，记录解除依据，仅将对应 blocked task/step 转回 `pending`（phase 重新聚合），再计算动作。条件未解除则保留 blocked 并停止。三次无进展阻塞需有实际修复或新诊断证据，重复调用本身不能清零计数。
- 质量链中的修复动作（简化修复、缺陷修复、CI 修复）失败时按各自契约重试；同一失败连续三次无新证据写 `blocked` 并停止。
- pipeline 不读取、不修改 `.ai/task/[feature]/`，不生成 manifest 或 item。
