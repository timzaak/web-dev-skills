---
name: t-push
description: 由 AI 基于 git diff 总结提交内容，使用脚本运行受影响区域 CI，通过后 git commit && git push。
allowed-tools:
  - Bash
---

# Push with Local CI

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`

提交前输入门禁、调用模式和中断恢复统一参考 `${CLAUDE_PLUGIN_ROOT}/protocols/push-execution-contract.md`；执行脚本前读取。

## Fixed Flow

先由 AI 读取 `git status --short` 和必要的 `git diff`，识别本次变更涉及的源码文件。

按目标项目 AGENTS.md 与已确认工程规则核对本次变更，再基于实际 diff 生成简洁 commit message；插件不规定代码注释策略。

然后为本次 `/t-push` 执行生成一个新的 session id（例如 `YYYYMMDD-HHMMSS` 或短 UUID），并调用脚本：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --ci-session "<本次 t-push session id>" --message "<AI 生成的 commit message>"
```

session 规则只说一次：同一次 `/t-push` 执行内（含 CI 失败后 AI 修复重跑）复用同一 session id；新的 `/t-push` 执行必须生成新 session id，避免复用上一次的区域通过缓存。

脚本负责：检测 项目与 Demo 变更范围并为受影响区域并发运行本地 CI（区域 CI 内容见下节）；按 session 记录每个区域通过 CI 时的 diff 指纹，重跑时已通过且 diff 未变的区域直接跳过；CI 全部通过后执行 `git add -A`、`git commit` 和推送目标分支。无 diff 时仍核对并补推现有 commit。未提交变更需要 `--message`。

## CI Rules

- 项目变更（demo/、.ai/ 以外）：运行目标项目 scripts/ci.py，脚本内部调用项目真实门禁；入口缺失或失败时停止，不静默跳过。
- demo/ 变更：在 demo/ 运行 npm run lint 与 npm run type-check；项目共享输入变化且存在 Demo 时同样重验 Demo。
- 只有 .ai/ 工作流产物变化时可无 CI；无 diff 时仍按共享契约恢复未推送 commit。
- 缓存指纹覆盖项目源码、配置与 CI 入口；同一 session 输入变化使缓存失效。

`--force-checks` 参数可忽略 session 缓存，强制重跑本次 diff 涉及的所有区域 CI。

## Failure

- 任一 CI 步骤失败：脚本停止且不 commit/push，并输出失败区域和步骤；AI 根据错误信息修复代码后，用同一 session id 重新运行脚本，直到通过。
- commit/push 失败：脚本停止并报告错误；按共享契约用同一 session 恢复本地 commit 并确认远端，不生成重复提交；代码变化时先重新验证和验收。
