---
name: t-code-review
description: |
  Run a high-signal local code review modeled after Claude Code's /code-review command.
  Reviews the current diff, a PR, a branch, a ref range, or a path; focuses on correctness
  bugs and scoped AGENTS.md/CLAUDE.md/REVIEW.md compliance; validates findings before reporting.
argument-hint: "[target] [--comment] [--fix]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Bash
  - Agent
---

# 代码审查

参考 Claude Code 官方 `/code-review` 的审查方式，在本地对当前改动或指定目标做高信号代码审查。默认只输出审查结果，不改代码、不运行构建、不提交 GitHub 评论。

## 使用场景

- 用户执行 `/t-tools:t-code-review`
- 用户要审查当前分支、工作区 diff、PR、分支、ref range 或指定文件
- `/t-run` 完成后，进入 Demo / E2E 前做一次实现质量审查

不要用于 PRD、设计、任务文档验收；这些阶段使用对应的 `t-*-check` 或 `t-demo-accept`。

## 参数

命令格式：

```text
/t-tools:t-code-review [target] [--comment] [--fix]
```

- `target` 可选：文件路径、PR 编号、分支名、ref range（如 `main...feature`）。未提供时审查当前分支相对 upstream/default branch 的提交，加 staged/unstaged 改动。
- `--comment` 可选：只在能确定当前目标是 GitHub PR 且 `gh` 可用时，才尝试发布评论；否则只输出本地结果。
- `--fix` 可选：先完成审查并展示 findings，再询问用户是否应用修复；未确认前不得修改文件。

## 审查范围

默认范围按顺序确定：

1. 如果传入 PR 编号，使用 `gh pr view` 和 `gh pr diff` 获取 PR 标题、描述和 diff。
2. 如果传入 ref range、分支或路径，使用对应 `git diff` / 文件内容作为审查范围。
3. 如果未传目标，优先使用当前分支 upstream；没有 upstream 时使用 default branch；仍不可用时使用 `HEAD` 加工作区改动。

必须只审查本次目标引入或修改的代码。不要报告目标外的既有问题，除非它直接证明本次改动引入了回归。

## 指令文件

审查前收集相关规则文件路径及内容：

- 仓库根目录 `AGENTS.md`、`CLAUDE.md`、`REVIEW.md`
- 被修改文件所在目录及其父目录中的 `AGENTS.md`、`CLAUDE.md`、`REVIEW.md`

规则适用范围按路径层级决定：目录内规则只约束该目录及子目录。`REVIEW.md` 是审查专用规则，优先级高于通用工程指令；`AGENTS.md` 和 `CLAUDE.md` 只在规则明确适用于审查时才作为 finding 依据。

## 工作流程

### 1. 建立审查上下文

- 读取 git 状态、目标 diff、修改文件列表和当前分支信息。
- 对 PR 目标读取标题和描述，作为作者意图上下文。
- 判断是否应跳过：closed PR、draft PR、自动依赖升级、明显平凡且正确的改动，或已由本 reviewer 审查过且无新 diff。
- 跳过时直接说明原因，不输出模拟 findings。

### 2. 并行审查

可使用 subagent 并行审查；每个 subagent 都必须拿到目标 diff、PR/变更摘要、相关规则文件路径和内容。

审查角色：

- 规则审查 A：检查 `AGENTS.md` / `CLAUDE.md` / `REVIEW.md` 中明确适用的规则是否被本次改动违反。
- 规则审查 B：独立重复规则审查，降低漏报。
- Bug 审查 A：只看 diff 本身，找明显 correctness bug；不读额外上下文，不做风格建议。
- Bug 审查 B：结合必要的局部上下文，找本次改动引入的安全、逻辑、边界条件或回归问题。

审查目标是高信号问题。只报告：

- 会导致编译、解析或运行失败的明确错误。
- 会稳定产生错误结果的清晰逻辑 bug。
- 安全、权限、数据泄露、租户隔离、事务一致性、迁移兼容性等会影响生产行为的问题。
- 明确、可引用、且路径作用域正确的规则违反。

不要报告：

- 纯风格、命名、格式、文档、泛泛质量建议。
- CI、lint、formatter、typechecker 会稳定捕获的问题，除非它也说明了更深层行为 bug。
- 缺测试这类通用质量问题，除非 `REVIEW.md` 明确要求或缺失会让本次行为无法验证。
- 需要大量假设才能成立的问题。
- 本次改动未触及行上的既有问题。
- 作者意图内的行为变化，除非实现与意图矛盾。

### 3. 验证与过滤

对每个候选 finding 做二次验证：

- 必须能指向真实文件和行号。
- 必须说明为什么这是本次改动引入或暴露的问题。
- 规则类 finding 必须引用具体规则，并确认该规则按路径层级适用于目标文件。
- bug 类 finding 必须用代码路径、数据流、状态变化或边界条件证明问题会发生。

只保留高置信、会影响实际行为的问题。

### 4. 输出

输出必须先列 findings，按严重度排序。格式：

```text
### Code review

Found N issues:

1. [Important] <一句话说明>
   - File: <path>:<line>
   - Evidence: <为什么成立>
   - Fix: <建议方向>

2. [Nit] <一句话说明>
   - File: <path>:<line>
   - Evidence: <为什么成立>
   - Fix: <建议方向>
```

如果没有问题，输出：

```text
### Code review

No issues found. Checked for bugs and scoped AGENTS.md/CLAUDE.md/REVIEW.md compliance.
```

严重度：

- `Important`：合并前应修复的 correctness、安全、数据、权限或回归问题。
- `Nit`：明确规则要求或低风险问题，值得修但不阻塞。
- `Pre-existing`：不是本次改动引入，但被本次 diff 明确暴露；默认不报告，除非对当前改动决策必要。

## `--comment`

只有同时满足以下条件才允许发 GitHub 评论：

- 用户传入 `--comment`。
- 当前目标能确定为 GitHub PR。
- `gh` 已认证且能读取/评论该 PR。
- findings 已完成二次验证。

没有 `--comment` 时，审查到这里就停止，不要发评论。

## `--fix`

`--fix` 不代表直接改文件。必须先输出审查结果，再询问用户是否修复哪些 finding。用户确认后才按最小范围修改，并在修改后运行与改动相关的最小验证。

## 收尾输出

完成后说明：

- 审查目标
- findings 数量与最高严重度
- 是否发布 GitHub 评论
- 如果使用 `--fix`，说明是否已修改文件和执行了哪些验证

## 失败处理

- 非 git 仓库：终止并提示必须在目标项目 git 仓库中运行。
- 无法确定 diff：提示用户传入文件路径、PR 编号、分支或 ref range。
- `gh` 不可用或未登录：降级为本地 diff 审查；如用户传了 `--comment`，说明无法评论。
- diff 过大：先按文件类型和风险排序审查关键路径；明确说明未覆盖的低风险文件。
- 规则文件冲突：优先更近路径的规则；`REVIEW.md` 优先于通用指令；仍冲突时在输出中列为 open question，不要伪造结论。
