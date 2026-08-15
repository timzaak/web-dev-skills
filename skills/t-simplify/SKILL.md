---
name: t-simplify
description: Review recent code changes for reuse, simplification, efficiency, and altitude issues with 4 parallel read-only reviewers, then apply the fixes directly. Quality cleanup only, not bug hunting. Replicated from Claude Code built-in /simplify.
argument-hint: "[focus 说明（可选，如 focus on memory efficiency）]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Edit
  - Write
  - Agent
---

# 变更代码清理

`t-simplify → 4 个清理审查 agent 并行 → 直接应用修复`

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`

## 来源说明

本 skill 复刻自 Claude Code 内置 `/simplify` 命令的提示词（[Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) 从二进制提取，MIT，v2.1.154 主提示词 + v2.1.213 内联降级版）。原文中四个角度指引是运行时注入变量、未随提取发布，本仓库按公开行为还原补全，落在 `${CLAUDE_PLUGIN_ROOT}/protocols/simplify-cleanup-contract.md`；并按本插件约定补充分 agent 角色规范、结构化契约和 `.ai/quality/` 报告。

## 目标

- 提升本次变更代码的质量，不是找 bug：从复用、简化、效率、抽象层级四个角度审查并直接修复。
- 不找正确性缺陷——那是 `/code-review` 与各阶段 accept 的职责。
- 修复保持行为不变：改变预期行为的修法一律跳过。

## 使用方式

```bash
/t-tools:t-simplify [focus 说明]
```

| 参数 | 说明 |
|---|---|
| `[focus 说明]` | 可选侧重点（如 `focus on memory efficiency`），透传给每个 reviewer 调整优先级，不缩小审查范围 |

推荐位置：`/t-run`（或 `/t-super-run`）完成实现与测试后、`/t-push` 提交前。

## 共享契约

审查角度定义、finding 结构、去重/跳过/修复边界和报告结构统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/simplify-cleanup-contract.md`

## 变更收集

- git 仓库且有提交：以 `git diff HEAD` 为审查范围（覆盖 staged + unstaged 的 tracked 变更），并用 `git status --porcelain` 把 untracked 源码文件纳入范围。
- 非 git 仓库或尚无提交：取最近修改的源码文件（排除 `.ai/`、`docs/`、构建产物、依赖目录等非源码路径）。
- 审查范围为空时返回 `NO_CHANGES`，不做任何修改。

## 执行流程

### Phase 1 — 审查（4 个清理 agent 并行）

1. 按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`，先 Read `${CLAUDE_PLUGIN_ROOT}/agents/simplify-reviewer.md` 全文（同批次复用，见该协议的 token 优化规则）。
2. 通过 `Agent` tool 在**同一条消息**里启动 4 个 `simplify-reviewer` sub agent，使其并行执行。每个 prompt 包含：
   - agent 角色规范全文（作为首段角色指令段）
   - 一个角度的完整指引（从 `${CLAUDE_PLUGIN_ROOT}/protocols/simplify-cleanup-contract.md` 摘取：Reuse / Simplification / Efficiency / Altitude 各一个，不重复、不遗漏）
   - 变更文件清单和获取完整 diff 的命令
   - focus 说明（如有）
3. 每个 reviewer 返回 findings：`file`、`line`、单行 `summary`、具体 `cost`（什么被重复、浪费或更难维护）。

### Phase 2 — 应用修复

1. 等待全部 4 个 agent 完成，按契约去重：指向同一行或同一机制的发现合并。
2. 直接修复剩余发现；每条修复前按 `${CLAUDE_PLUGIN_ROOT}/protocols/simplify-cleanup-contract.md` 的 Skip Rules 判断是否跳过。
3. 修复后运行能覆盖所改文件的最小定向验证（编译/类型检查/相关测试）；验证失败时回退该条修复并记为跳过。
4. 按契约把报告写入 `.ai/quality/simplify-[YYYYMMDD-HHMMSS].md`，并以简要总结收尾：修了什么、跳了什么（含原因），或确认代码已干净。

## Inline 降级

`Agent` tool 在当前上下文不可用时，不终止：主会话在当前上下文按四个角度**单遍**依次审查全部变更，不得因无法并行而跳过任何角度；Phase 2 与报告要求不变，且报告和总结必须声明这是单主会话单遍审查、不是 4-agent 并行审查。

## 错误处理

| 错误码 | 触发条件 | 用户可见提示 | 恢复动作 |
|---|---|---|---|
| `NO_CHANGES` | 变更收集结果为空 | 没有可审查的变更 | 先实现变更后再运行 |
| `AGENT_UNAVAILABLE` | Agent tool 不可用 | 已切换为单遍 inline 审查 | 无需恢复；报告会如实声明 |
| `DIFF_TOO_LARGE` | 变更规模超出单次可审查范围 | 变更过大，建议缩小范围 | 按文件分批运行，或先提交部分变更 |

## Forbidden

- 找正确性 bug、提出会改变预期行为的修复。
- 修复需要明显超出本次审查 diff 的改动（共享 helper 新建除外，见契约 Skip Rules）。
- reviewer sub agent 修改代码或文档。
- 跳过任何审查角度，或串行分批启动本应并行的 4 个 reviewer。
- 把 inline 降级审查冒充 4-agent 并行审查写入报告。

## 示例

```bash
/t-tools:t-simplify
/t-tools:t-simplify focus on memory efficiency
```

输出：

```text
已修复 3 项，跳过 1 项（超出本次 diff 范围）
- src/api/users.rs:42 | Reuse | 重复实现既有 validate_tenant | 改用 shared/tenancy::validate
- src/api/users.rs:88 | Simplification | 单调用方的间接包装层 | 内联展开
- web/src/routes/posts.tsx:31 | Efficiency | 列表 render 内逐项新建排序数组 | 提出循环并 memo
- 跳过: src/domain/order.rs:120 | Altitude | 共享函数新增特例分支 | 修复需重构底层机制，超出范围
报告: .ai/quality/simplify-20260815-103000.md
```
