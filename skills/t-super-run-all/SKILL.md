---
name: t-super-run-all
description: Unattended pipeline that runs ALL remaining delivery phases of a feature in one invocation. Each phase executes the t-super-run loop (outcome-level planning, main-session dev/test, read-only accept), then the quality chain review --fix -> simplify -> push, before moving to the next phase. Use after design is complete for end-to-end execution; use t-super-run for a single phase, t-task/t-run for item-based subagent execution.
argument-hint: "[任务名称]"
allowed-tools:
  - Agent
  - AskUserQuestion
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash
  - WebSearch
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
  - mcp__chrome-devtools__list_pages
  - mcp__chrome-devtools__select_page
  - mcp__chrome-devtools__take_snapshot
  - mcp__chrome-devtools__take_screenshot
  - mcp__chrome-devtools__list_console_messages
  - mcp__chrome-devtools__get_console_message
  - mcp__chrome-devtools__list_network_requests
  - mcp__chrome-devtools__get_network_request
---

# Super Run All

设计定稿后的无人值守连跑入口：按规范顺序把剩余全部 active phase 一次跑完。每个 phase 先执行 `t-super-run` 的阶段闭环（目标级计划、主会话实现与测试、只读 accept 收口），再执行质量链 `t-review --fix -> t-simplify -> t-push`，全部通过后才进入下一个 phase。review 紧跟 accept 审同一份实现，缺陷修复完成后再做行为不变的质量清理。

用户的一次手工调用即授权整条链；phase 与质量链是本 skill 的内部步骤，按各自契约执行，不构成自动触发其它 `t-*` 命令。`t-prd-publish` 和 `t-release` 不在链内。

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`

pipeline 接力、质量链与游标规则统一参考：

- `${CLAUDE_PLUGIN_ROOT}/protocols/super-run-all-pipeline.md`

phase 内来源加载、计划、状态、执行与验收规则统一参考：

- `${CLAUDE_PLUGIN_ROOT}/protocols/super-run-state-contract.md`

需求与决策边界统一参考：

- `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`

规划测试与验收时读取 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`；pipeline 收尾按同一协议核对证据和待验证项。

## 参数

| 参数 | 说明 |
| --- | --- |
| `[feature]` | 必填；必须是单个目录名，允许中文、英文、数字、空格、下划线和连字符，拒绝路径分隔符、`.` 和 `..` |

## 前置条件

- `.ai/design/[feature].md` 必须存在，且首次运行 `python "${CLAUDE_PLUGIN_ROOT}/scripts/check-design.py" ".ai/design/[feature].md" --require-complete --json` 通过；失败时停止并提示先运行 `/t-design <feature>`。`t-prd-check`、`t-design-check`、`t-task-check` 均不是强制前置。
- 启动前完成 preflight，把所有需要人的输入一次收齐，链上不再中途询问：
  1. 展示按设计将要连跑的 phase 顺序（`backend -> frontend -> extension -> miniapp -> flutter -> web-demo -> extension-demo -> flutter-demo` 的命中子集）。
  2. 按 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md` 确认无未裁决的用户决策；存在时先解决再启动。
  3. demo phase 需要的环境参数（Flutter `--device`、扩展浏览器接入、context7 MCP）在此确认；缺失即停止，不在链中途补问。
- 不读取或修改 `.ai/task/[feature]/`。
- 已有 `.ai/super-run/[feature]/.pipeline.json` 损坏或结构非法时停止并保留原文件，不自动重建。

## 执行循环

每轮迭代先按 pipeline 契约的 Push 前门禁核对来源和已完成证据，再运行下一步计算，按返回的 `action` 执行；禁止凭内存中的 phase 列表推进：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/super-run-next.py" "<feature>" --json
```

- `plan_first_phase`：按 `super-run-state-contract` 的来源加载与计划规则识别 `active_phases`、创建 `.state.json` 和首个 phase 计划，然后执行该 phase。
- `run_phase`：按 `super-run-state-contract` 完整执行或恢复该 phase 的闭环（来源加载、计划与状态、执行循环、完成条件全部继承）；phase 聚合为 `completed | skipped` 后进入质量链。
- `reset_quality`：按 pipeline 的输入绑定与失效规则重置指定 phase 的质量链，再重算动作。
- `check_blocked`：按 pipeline 的失败与恢复规则先复核解除条件；有新证据时只恢复对应 task/step，无变化则保留 blocked 并停止，不能直接重试。
- `review`：首次绑定脚本返回的 `input_fingerprint`，先写 `in_progress`，读取 `${CLAUDE_PLUGIN_ROOT}/skills/t-review/SKILL.md` 并按 `--fix` 模式完整执行；完整发现集存在未修复的 CONFIRMED 或阻塞级未决 PLAUSIBLE 时不得写 `completed`，需要用户裁决时写 `blocked`。
- `simplify`：先把 `.pipeline.json` 对应 step 写 `in_progress`，读取 `${CLAUDE_PLUGIN_ROOT}/skills/t-simplify/SKILL.md` 并按其完整流程执行，覆盖 review --fix 的修复代码；`NO_CHANGES` 视为完成。
- `push`：先写 `in_progress` 并持久化本 step 的 CI session，读取 `${CLAUDE_PLUGIN_ROOT}/skills/t-push/SKILL.md`；按 pipeline 的 Push 前门禁执行预检查、证据核对及必要重新验收，再带已验收指纹提交推送。失败按其恢复契约处理，远端确认目标 commit 后才写 `completed`。
- `status=done`：进入完成报告。
- `status=blocked` 或 `error`：停止并报告阻塞点、证据与恢复入口。

每个质量链步骤完成或失败后立即写回 `.pipeline.json`（含 `last_error` 与 `failures_without_progress`）；每次显著步骤后把进度写入状态或游标，确保上下文压缩或中断后同一条命令从磁盘状态续跑。

## 禁止事项

- 并行执行多个 phase 或质量链步骤；跳过、重排质量链，或在存在未修复正确性发现时执行 push。
- 修改 `.ai/task/` 状态或生成 manifest/item。
- 把 accept 改为实现角色，或弱化断言、忽略失败换取推进。
- 自动执行 `t-prd-publish`、`t-release` 或其它对外发布动作。
- 在 dev/test 中调用 `Agent` 或并行 subagent（继承 super-run 边界；accept 只允许串行派发计划中的只读 accept agent）。

## 完成条件

只有同时满足以下条件才报告 pipeline 完成：

- 全部 active phase 为 `completed | skipped`，且全部质量链步骤为 `completed`（skipped phase 除外）。
- 按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md` 核对全部必要场景均有有效证据；缺失时按该协议重新打开承接验收，不宣称交付完成。

输出各 phase 状态、主要变更、质量链结果（简化项、审查发现与修复、push 记录）和剩余人工步骤（`t-prd-publish`、`t-release`），然后停止本次调用。

## 失败处理

- phase 或质量链步骤 `blocked`：先复核解除条件，仍阻塞时停止，报告阻塞点、证据与建议的用户裁决。
- 同一质量链步骤连续三次失败且无新证据：写 `blocked` 并停止，不用无界重试掩盖阻塞。
- `super-run-next.py` 返回 `error`（状态或游标损坏、结构非法）：停止并保留原文件，恢复方案需先由用户确认。
- 设计指纹变化按 `super-run-state-contract` 的 Design Source Gate 处理（重读设计、只重开受影响 task），不额外停车；无法确定影响范围时按该协议停止并请求用户裁决。
