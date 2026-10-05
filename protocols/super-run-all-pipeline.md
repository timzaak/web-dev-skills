# Super Run All Pipeline Contract

`t-super-run-all` 的跨 phase 接力、每阶段质量链与 pipeline 游标的单一事实源。

phase 内的计划、状态、执行与验收以 `${CLAUDE_PLUGIN_ROOT}/protocols/super-run-state-contract.md` 为准；phase 启用与默认顺序以 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 为准。本契约只定义跨 phase 接力和质量链，不重复它们的内容。

## Pipeline 范围

- 输入为设计已 `complete` 的 feature；连跑范围取 `.ai/super-run/<feature>/.state.json` 的 `active_phases`。
- 每个按规范顺序选出的 phase 依次执行：super-run phase 闭环 → `review(--fix)` → `simplify` → `push`；全部通过后进入下一个 phase。review 紧跟 accept，两个正确性结论作用于同一份实现；simplify 的行为不变契约与定向验证保证其后的清理不失效正确性结论。
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
      "review": {"status": "completed"},
      "simplify": {"status": "in_progress", "failures_without_progress": 0},
      "push": {"status": "pending", "last_error": null}
    }
  }
}
```

- `chain` 固定为 `["review", "simplify", "push"]`，不允许跳过或重排。
- step 状态只允许 `pending | in_progress | failed | blocked | completed`。
- 失败时记录 `last_error`；`failures_without_progress` 持久化在当前 step，实质进展后才能清零，同一失败连续三次无新证据转 `blocked`。
- 不记录时间类元数据。
- 游标只由 `t-super-run-all` 创建和更新；损坏或结构非法时停止并保留原文件，不自动重建。

## 质量链步骤

每步开始前写 `in_progress`，结束后写 `completed` 或失败原因：

- **review**：按 `${CLAUDE_PLUGIN_ROOT}/skills/t-review/SKILL.md` 的 `--fix` 模式及 `${CLAUDE_PLUGIN_ROOT}/protocols/review-correctness-contract.md` 完整执行；只有报告无未修复的 CONFIRMED 发现、且无阻塞级未决 PLAUSIBLE 时才可写 `completed`，未决项需要用户裁决时写 `blocked`。
- **simplify**：按 `${CLAUDE_PLUGIN_ROOT}/skills/t-simplify/SKILL.md` 及 `${CLAUDE_PLUGIN_ROOT}/protocols/simplify-cleanup-contract.md` 完整执行，覆盖 review --fix 的修复代码；`NO_CHANGES` 视为完成。
- **push**：按 `${CLAUDE_PLUGIN_ROOT}/skills/t-push/SKILL.md` 执行注释清理、commit message 总结与 `push.py` 调用；CI 或 push 失败按该 skill 的失败规则修复后重跑。push 失败但本地 commit 已保留时，不得绕过失败直接标记完成。

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
| `none` | 无可执行动作；`status` 为 `done` 表示全部完成 |
| `none` + `status=blocked` / `status=error` | 停止并报告原因 |

脚本只读状态并计算下一步，不写任何文件。

## 停止条件

只有以下情况停止：

- phase 聚合为 `blocked`，或质量链步骤为 `blocked`。
- `super-run-next.py` 返回 `error`（状态或游标损坏、结构非法）。
- demo phase 缺运行环境；按对应 demo 指南补齐后重跑同一命令恢复。
- 全部 phase 与质量链完成。

设计指纹变化按 super-run 共享协议处理（重读设计、重开受影响 task），不额外停车。

## 失败与恢复

- 中断后重跑同一命令：`super-run-next.py` 从磁盘状态重算，已完成的 phase 与质量链步骤不重复执行。
- 质量链中的修复动作（简化修复、缺陷修复、CI 修复）失败时按各自契约重试；同一失败连续三次无新证据写 `blocked` 并停止。
- pipeline 不读取、不修改 `.ai/task/[feature]/`，不生成 manifest 或 item。
