---
name: t-review
description: Review the changed code for correctness bugs with 3 parallel read-only finder agents (line-by-line scan, removed-behavior audit, cross-file tracing) plus a 1-vote 3-state verify pass, then write an evidence-backed findings report. Report-only by default — no fixes and no cleanup; quality cleanup belongs to t-simplify. With --fix, confirmed findings are additionally repaired after the report is written. The default scope is the upstream range plus uncommitted changes; a PR / branch / file target replaces it.
argument-hint: "[<target>（可选：PR 号 / 分支名 / 文件路径）] [--fix]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - Edit
  - Agent
---

# 变更代码正确性审查

`t-review → 3 个正确性 finder agent 并行 → 1 个 verifier 三态验证 → 报告（--fix 时追加修复）`

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（判断脚本入口或项目事实与插件默认冲突时读）

## 目标

- 找出本次变更引入的正确性缺陷：逐行扫描、删除行为审计、跨文件追踪三个角度并行审查，经独立验证后输出可复核报告。
- 默认只报告不修复：缺陷修复属于 dev 职责（`t-super-run` 或主会话确认后执行）；传入 `--fix` 时在报告写入后按修复模式处置全部保留发现。
- 不做质量清理——复用/简化/效率/抽象层级属于 `/t-tools:t-simplify`。

## 使用方式

```bash
/t-tools:t-review [<target>] [--fix]
```

| 参数 | 说明 |
| --- | --- |
| `[<target>]` | 可选审查目标（PR 号 / 分支名 / 文件路径）；传入时直接替换默认审查范围，提示词以 `Review target: \`<target>\`` 前缀注入 |
| `--fix` | 修复模式：报告写入后修复 CONFIRMED 发现并处置 PLAUSIBLE 发现，修复结果追加进同一报告；不改变审查与验证流程本身 |

推荐位置：`/t-super-run` 完成实现与测试后、`/t-tools:t-simplify` 之前；`/t-tools:t-push` 提交前是最后窗口。`t-super-run-all` 的质量链在 simplify 之前以 `--fix` 模式执行本命令。

## 共享契约

角度定义、候选结构、Pass-Through、去重/三态验证和报告结构统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/review-correctness-contract.md`

## 变更收集

按 Phase 0 语义收集审查范围（与 t-simplify 同源）：

1. 优先 `git diff @{upstream}...HEAD`；无 upstream 时依次回退 `git diff main...HEAD`、`git diff HEAD~1`。
2. 存在未提交变更、或区间 diff 为空时，追加 `git diff HEAD` 把工作区变更纳入范围（审查常发生在提交前）；untracked 源码文件一并纳入（插件补充）。
3. 用户传入 `<target>`（PR 号 / 分支名 / 文件路径）时，以该目标为审查范围，替换上述默认收集。
4. 非 git 仓库或尚无提交：取最近修改的源码文件（排除 `.ai/`、`docs/`、构建产物、依赖目录等非源码路径；插件补充）。
5. 审查范围为空时返回 `NO_CHANGES`，不做任何修改。

## 执行流程

### Phase 1 — 发现（3 个 finder agent 并行）

1. 按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`，先 Read `${CLAUDE_PLUGIN_ROOT}/agents/review-finder.md` 全文（同批次复用，见该协议的 token 优化规则）。
2. 通过 `Agent` tool 在**同一条消息**里启动 3 个 `review-finder` sub agent，使其并行执行。每个 prompt 包含：
   - agent 角色规范全文（作为首段角色指令段）
   - 一个角度的完整指引（从 `${CLAUDE_PLUGIN_ROOT}/protocols/review-correctness-contract.md` 摘取：Angle A / B / C 各一个，不重复、不遗漏）
   - 变更文件清单和获取完整 diff 的命令
3. 每个 finder 返回最多 6 条候选：`file`、`line`、单行 `summary`、具体 `failure_scenario`。
4. 高风险或大范围变更（安全敏感、并发、公共 API 变更）时，在启动前决定追加 Angle D / E 两个 finder（见契约扩展角度），不得中途追加。

### Phase 2 — 验证与报告

1. 聚合全部候选，按契约 Dedup 规则去重。
2. Read `${CLAUDE_PLUGIN_ROOT}/agents/review-verifier.md` 全文，启动 1 个 `review-verifier` sub agent，注入全部去重后候选与获取 diff 的命令，逐条获得 CONFIRMED / PLAUSIBLE / REFUTED。
3. 保留 CONFIRMED 与 PLAUSIBLE，按严重度排序、上限 8 条，按契约把报告写入 `.ai/quality/review-[YYYYMMDD-HHMMSS].md`。
4. 以简要总结收尾：几项确认、几项存疑、排除了多少误报；有发现时给出修复入口建议（t-super-run / 主会话修复后可重跑复核），无发现时明确"未发现正确性缺陷"。
5. 传入 `--fix` 时继续执行 Phase 3 — 修复。

### Phase 3 — 修复（仅 `--fix`）

报告写入后处置全部保留发现；Phase 1/2 与报告内容保持只读不变：

1. PLAUSIBLE 发现先按其 `failure_scenario` 尝试复现或确认；能确认的视同 CONFIRMED 处置，无法确认的保留为 pending 并写明确认途径。
2. CONFIRMED 发现由主会话切换到受影响端的 dev 角色边界修复：读取对应 `agents/<端>-dev.md` 作为当前角色边界（与 `t-super-run` 的主会话角色切换一致），不为此新派 subagent。
3. 会改变预期行为的修法一律跳过并标记 pending（属设计或需求问题，需用户裁决），不得通过改变需求含义消除缺陷。
4. 每条修复后立即运行覆盖所改文件的最小定向验证（编译/类型检查/相关测试）；验证失败时继续修复或回退该条并标记 pending。
5. 全部处置完（fixed / pending）后在同一报告追加 `## Fixes`：逐条列出 fixed（修复说明与验证命令）、pending（原因或确认途径）；总结必须写明剩余 pending 数量。
6. 同一发现连续三次修复失败且无新证据：标记 blocked 并停止，保留失败证据。

## Inline 降级

`Agent` tool 在当前上下文不可用时，不终止：主会话在当前上下文按三个角度**单遍**依次审查全部变更，不得因无法并行而跳过任何角度；每条候选自行对照 diff 复核，只保留能给出具体 failure_scenario 的项（无独立 verifier）。报告要求不变，且报告和总结必须声明这是单主会话单遍审查、未经独立验证。

## 错误处理

| 错误码 | 触发条件 | 用户可见提示 | 恢复动作 |
|---|---|---|---|
| `NO_CHANGES` | 变更收集结果为空 | 没有可审查的变更 | 先实现变更后再运行 |
| `AGENT_UNAVAILABLE` | Agent tool 不可用 | 已切换为单遍 inline 审查 | 无需恢复；报告会如实声明 |
| `DIFF_TOO_LARGE` | 变更规模超出单次可审查范围 | 变更过大，建议缩小范围 | 按文件分批运行，或先提交部分变更 |

## Forbidden

- 默认模式（未传 `--fix`）修复发现的缺陷，或在审查与验证（Phase 1/2）过程中修改任何代码；`--fix` 的修复只发生在报告写入之后。
- 用弱化断言、放宽校验、删除断言或改需求含义的方式消除发现。
- 改写、降级或代出 finder / verifier 的结论。
- 展开质量清理分析——发现清理线索只转交 t-simplify。
- finder 或 verifier sub agent 修改代码或文档。
- finder 静默过滤 failure_scenario 可命名的候选（绕过验证是漏报主因）。
- verifier 无证据 REFUTED、遗漏候选或把多条候选合并判定。
- 跳过任何审查角度，或串行分批启动本应并行的 finder。
- 把 inline 降级审查冒充多 agent 审查写入报告。

## 示例

```bash
/t-tools:t-review
/t-tools:t-review feat/user-management
/t-tools:t-review src/api/orders.rs
/t-tools:t-review --fix
```

输出：

```text
2 项 CONFIRMED，1 项 PLAUSIBLE，已排除 2 项误报
- src/api/users.rs:42 | A | CONFIRMED | 分页参数 falsy-zero 被当缺失处理 | skip=0 时整页数据被跳过
- src/api/users.rs:118 | C | CONFIRMED | 调用方未适配新的 Result 返回 | orders.rs:31 直接解包 panic
- src/domain/order.rs:60 | B | PLAUSIBLE | 删除的余额守卫未在别处重建 | 并发扣减可能透支，需复现确认
- 已排除: src/api/users.rs:7 | A | REFUTED | 解引用前已有非空守卫（users.rs:39）
报告: .ai/quality/review-20260815-104500.md
```
