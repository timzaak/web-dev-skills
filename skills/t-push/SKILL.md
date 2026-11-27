---
name: t-push
description: 由 AI 基于 git diff 总结提交内容，使用脚本运行受影响区域 CI，通过后 git commit && git push。
allowed-tools:
  - Bash
---

# Push with Local CI

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`；确定性操作由 `${CLAUDE_PLUGIN_ROOT}/scripts/push.py` 执行。

## Fixed Flow

先由 AI 读取 `git status --short` 和必要的 `git diff`，识别本次变更涉及的源码文件。

在生成 commit message 和调用脚本前，AI 必须清理本次变更源码文件中的注释。先运行预筛脚本取得候选清单：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/comment-audit.py
```

脚本只读不改，从本次未提交变更输出 JSON 候选：`remove-candidate`（命中禁止条款，含变更文件内 diff 未触及的存量违规，`scope=existing`）默认删除，除非能指认"必须保留"类别；`review-candidate`（注释密度超标文件的注释）与其余 diff 新增注释一样，逐条对照"必须保留"类别，命中不了就删除。判定标准以 `${CLAUDE_PLUGIN_ROOT}/protocols/code-comment-contract.md` 为准，清理范围只限本次变更文件，不做全仓历史清理。

清理后重新查看必要的 `git diff`，逐条确认剩余的 diff 新增注释都能指认所属的保留类别（含未被脚本列出的新增注释），再总结本次变更并生成简洁 commit message。commit message 必须来自 AI 对清理后实际变更的总结，不能由脚本根据目录名自动猜测。

然后为本次 `/t-push` 执行生成一个新的 session id（例如 `YYYYMMDD-HHMMSS` 或短 UUID），并调用脚本：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/push.py --ci-session "<本次 t-push session id>" --message "<AI 生成的 commit message>"
```

session 规则只说一次：同一次 `/t-push` 执行内（含 CI 失败后 AI 修复重跑与中断恢复）复用同一 session id；新的 `/t-push` 执行必须生成新 session id，避免复用上一次的区域通过缓存。`--force-checks` 忽略当前 session 的 CI 缓存。

脚本负责：检测 backend/frontend/extension/demo/shopify 变更范围并为受影响区域并发运行本地 CI；按 session 记录每个区域通过 CI 时的 diff 指纹，重跑时已通过且 diff 未变的区域直接跳过；CI 全部通过后执行 `git add -A`、`git commit` 和推送目标分支。无 diff 时仍核对并补推现有 commit。未提交变更需要 `--message`。

## Commit Message 规范

默认单行，格式为 Conventional Commits `<type>(<scope>): <description>`，type 取 `feat / fix / docs / style / refactor / perf / test / chore`，scope 可省略：

- description 用祈使句陈述应用该提交后的效果（补全 `"If applied, this commit will …"` 应当成句），整行不超过 72 字符，不以句号结尾；放不下时收窄描述，不放宽长度。
- 默认不写 body。仅当 diff 自身解释不了的动机、破坏性影响或使用方必须知道的后续动作存在时才补 body，且只写 why 和外部影响，不写 how；与 subject 空行分隔，每行不超过 72 字符。不复述文件清单或逐条改动明细。
- 示例：`feat(figma-assets): derive transparency from reference PNGs`；反例：`feat: update asset pipeline` 后跟多条 bullet 复述改了哪些文件。

## CI Rules

- Backend 变更：`cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features -- -D warnings`、`cargo fmt --all`，再以不带 `--fix` 的 `cargo clippy --all-targets --all-features -- -D warnings` 终验。
- Frontend 变更：`npm run lint`、`npm run format:check`（不存在时跳过）、`npm run type-check`。
- Demo 变更：`npm run lint` 和 `npm run type-check`。
- Extension 变更：`npm run lint`（不存在时跳过）和类型检查（兼容 `compile` / `type-check`，且不能缺失）。
- Shopify 变更（项目根存在 `shopify.app.toml` 时，除 `demo/` 外的全部变更）：按 `${CLAUDE_PLUGIN_ROOT}/guides/shopify/quality.md` 的 push 门禁执行，类型检查兼容 `typecheck` / `type-check` 且不能缺失；存在 Shopify 扩展配置时必须覆盖扩展构建。
- 无 backend/frontend/extension/demo/shopify 变更时跳过本地 CI，直接进入 commit/push。

## 工作区指纹、提交及恢复契约

- **工作区指纹**：SHA-256 覆盖 Git 管理及未忽略的未跟踪文件的路径、文件内容、符号链接目标和可执行位（删除文件不计入当前快照，不含 HEAD，排除 `.ai/`）。无法读取或确定文件类型时失败。指纹在 commit 前写入恢复记录，在 commit hook 之后及恢复补推时核对；commit hook 改变代码时保留本地 commit 及恢复记录，停止 push，交回验证闭环。
- **恢复记录**：在 Git 私有目录 `t-tools-push-ci/<session>-push.json` 原子写入，字段为 `status`、`branch`、`remote`、`ref`、`base_head`、`message`、`fingerprint`（commit 创建后追加完整 `commit`），状态为 `committing -> pending -> completed`；损坏时停止并保留文件。
- **提交与推送确认**：commit 前写 `committing`，成功后写目标 commit 与 `pending`，确认远端目标分支包含该 commit（通过实际远端祖先关系确认，不依赖本地 upstream 缓存）才写 `completed`。显式按记录中的 remote/ref 推送，不 force，不附带其他分支或发布动作；无 upstream 或 detached HEAD 时停止，先由用户配置目标。
- **中断恢复**：
  - commit 后、pending 写回前中断：仅在 HEAD 父提交等于 `base_head`、提交消息匹配且代码快照一致时认定为该次 commit，无法确定则停止；commit 未发生时重跑 CI 和门禁。
  - `pending` 恢复先核对分支、推送目标、HEAD 和代码快照，直接补推原 commit 不重复提交；`completed` 恢复也确认远端包含该 commit；工作区干净且无本 session 记录时也核对并推送当前 HEAD。
  - 记录后代码或目标改变时停止，须重新验证并重新验收后才能启动新 session，旧记录保留供复核。

## Failure

- 任一 CI 步骤失败：脚本停止且不 commit/push，并输出失败区域和步骤；AI 根据错误信息修复代码后，用同一 session id 重新运行脚本，直到通过。
- commit/push 失败：脚本停止并报告错误；按上述恢复契约用同一 session 恢复本地 commit 并确认远端，不生成重复提交；代码变化时先重新验证和验收。
