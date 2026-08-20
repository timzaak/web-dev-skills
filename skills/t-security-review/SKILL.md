---
name: t-security-review
description: Security review of the pending changes on the current branch. One read-only finder subagent identifies high-confidence vulnerabilities, then parallel read-only filter subagents reject false positives; only findings with confidence >= 8 reach the report. Review only, no fixes. Replicated from Claude Code built-in /security-review.
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Agent
  - Write
---

# 分支变更安全审查

`t-security-review → 1 个漏洞识别 agent → N 个误报过滤 agent 并行 → 置信度 >= 8 的发现写入报告`

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`

## 来源说明

本 skill 复刻自 Claude Code 内置 `/security-review` 命令的提示词，原文从本机 `@anthropic-ai/claude-code@2.1.232` 的 `claude.exe` 二进制内嵌字符串逐字提取（v2.1.232，非网上转述）。原文的动态 git 上下文注入、两级 sub-task 编排（先识别、再逐条并行误报过滤）、识别规则、误报过滤清单和 `confidence < 8` 丢弃规则均按原文语义保留，落在 `${CLAUDE_PLUGIN_ROOT}/protocols/security-review-contract.md`（原文 HARD EXCLUSIONS 存在两个 "16." 的编号笔误，契约中已连续重编号为 18 项，内容未改）。按本插件约定补充了 subagent 角色规范（`security-vuln-finder`、`security-fp-filter`）、`.ai/quality/` 报告产物、inline 降级和错误处理。

## 目标

- 识别当前分支待提交变更中**新引入**的高置信度安全漏洞，输出可交给安全团队执行的报告。
- 只审查不修复：本 skill 不修改任何业务代码。
- 不是通用代码审查：质量清理属于 `/t-tools:t-simplify`，正确性缺陷属于 `/code-review` 与各阶段 accept。

## 使用方式

```bash
/t-tools:t-security-review
```

无参数。推荐位置：`/t-run`（或 `/t-super-run`）完成后、`/t-push` 提交前，与 `/code-review --fix` 和 `/t-tools:t-simplify` 并列使用。

## 共享契约

漏洞识别指令、误报过滤指令、finding/裁定结构、置信度门槛和报告结构统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/security-review-contract.md`

## 变更收集

- 必须运行在 git 仓库内，否则返回 `NOT_GIT_REPO`（与原命令一致）。
- 审查范围是当前分支相对远端默认分支的待提交变更，按序取第一个可用的 diff 基准：`origin/HEAD` → `origin/main` → `origin/master`。
- 上下文命令（只读）：`git status`、`git diff --name-only <base>...`、`git log --no-decorate <base>...`、`git diff <base>...`。
- diff 为空时返回 `NO_CHANGES`，不启动任何 sub agent。

## 执行流程

### Phase 1 — 漏洞识别（1 个 sub agent）

1. 按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`，先 Read `${CLAUDE_PLUGIN_ROOT}/agents/security-vuln-finder.md` 全文（同批次复用）。
2. 通过 `Agent` tool 启动 1 个 `security-vuln-finder`，prompt 包含：agent 角色规范全文、契约"漏洞识别指令集"全文、上述变更收集命令清单。
3. 等待其返回结构化 findings。

### Phase 2 — 误报过滤（N 个 sub agent 并行）

1. Read `${CLAUDE_PLUGIN_ROOT}/agents/security-fp-filter.md` 全文。
2. 对 Phase 1 的**每条** finding，通过 `Agent` tool 在**同一条消息**里启动对应数量的 `security-fp-filter`，使其并行执行。每个 prompt 包含：agent 角色规范全文、契约"误报过滤指令集"全文、单条 finding 的完整内容及其定位上下文。
3. 收集每条 finding 的 `verdict` 与 `confidence`。

### Phase 3 — 聚合与报告

1. 丢弃 `confidence < 8` 的发现；剩余的按契约报告结构写入 `.ai/quality/security-review-[YYYYMMDD-HHMMSS].md`。
2. 以报告摘要收尾：确认 N 项（按严重度列出）、过滤 M 项，或确认未发现高置信度安全问题。不复述报告全文。

## Inline 降级

`Agent` tool 在当前上下文不可用时，不终止：主会话在当前上下文先按"漏洞识别指令集"完整识别一遍，再对每条发现按"误报过滤指令集"逐条独立复核（两遍分离，不得在同一步里边找边过滤）。置信度门槛与报告要求不变，且报告和总结必须声明这是单主会话两遍审查、不是识别 + 并行过滤的多 agent 审查。

## 错误处理

| 错误码 | 触发条件 | 用户可见提示 | 恢复动作 |
|---|---|---|---|
| `NOT_GIT_REPO` | 当前目录不是 git 仓库 | /security-review 需要在 git 仓库内运行 | `cd` 进仓库后重试 |
| `NO_CHANGES` | diff 为空 | 分支没有待审查的变更 | 先实现变更后再运行 |
| `AGENT_UNAVAILABLE` | Agent tool 不可用 | 已切换为单主会话两遍审查 | 无需恢复；报告会如实声明 |
| `DIFF_TOO_LARGE` | 变更规模超出单次可审查范围 | 变更过大，建议缩小范围 | 按文件分批运行，或先提交部分变更 |

## Forbidden

- 修复任何代码或文档；本 skill 只输出审查报告。
- 把 `confidence < 8` 的发现写进报告。
- 报告本次 diff 之外的仓库既有安全问题。
- sub agent 修改代码或文件；`security-fp-filter` 使用 Bash。
- 跳过误报过滤直接输出 Phase 1 findings。
- 把 inline 降级审查冒充多 agent 审查写入报告。

## 示例

```bash
/t-tools:t-security-review
```

输出：

```text
确认 2 项，过滤 3 项
- src/api/orders.py:88 | command_injection | HIGH | 订单导出参数未净化直接拼入 shell 命令
- web/src/routes/admin.tsx:31 | xss | MEDIUM | 角色名经 dangerouslySetInnerHTML 渲染
- 过滤: src/tasks/sync.py:12 | 依赖过时 (硬排除项 9)
- 过滤: src/api/health.py:9 | 无认证 (判例 8: 客户端代码)
报告: .ai/quality/security-review-20260820-143000.md
```
