# Push Execution Contract

供 `t-push` 和 `t-super-run-all` 消费的本地 CI、提交前输入门禁及推送恢复契约；CI 区域与工程命令由 `${CLAUDE_PLUGIN_ROOT}/skills/t-push/SKILL.md` 路由，确定性操作由 `${CLAUDE_PLUGIN_ROOT}/scripts/push.py` 执行。

## 调用模式

- 默认模式：`--ci-session <id> --message <text>`，对当前 diff 运行 CI，成功后提交并推送。message 由主会话依据最终 diff 生成。
- 预检查模式：`--ci-session <id> --check-only`，运行相同 CI（可能自动修复），输出 `Validated worktree fingerprint: sha256:<digest>`；不 commit、不 push，不要求 message。
- 已验收提交：默认模式增加 `--expected-fingerprint <digest>`。脚本在 CI 前、CI 后和 commit 前核对同一指纹；不匹配则失败，不提交推送。commit hook 改变代码时保留本地 commit 及恢复记录，停止 push，交回验证闭环。
- `--force-checks` 忽略当前 session 的 CI 缓存。新执行用新 session，重试和中断恢复复用同一 session；pipeline 将其持久化在 push step。

## 工作区指纹

SHA-256 覆盖 Git 管理及未忽略的未跟踪文件的路径、文件内容、符号链接目标和可执行位；删除文件不计入当前快照。摘要不含 HEAD，因此提交前后相同代码的指纹一致。`.ai/` 是工作流状态和证据产物，排除在代码指纹外，避免游标写回使已验收代码失效；其中来源、证据及环境仍由 verification-evidence-contract 单独核对。无法读取或确定文件类型时失败，不跳过未知输入。

该指纹证明提交代码与主会话绑定的快照一致，不证明业务正确。调用方必须先取得适用的运行证据和独立验收，再把预检查输出认定为已验收指纹。

## 提交及恢复

- 在 Git 私有目录 `t-tools-push-ci/<session>-push.json` 原子写入恢复记录，不写入业务代码或 `.ai/task/`；损坏时停止并保留文件。
- 记录字段为 `status`、`branch`、`remote`、`ref`、`base_head`、`message`、`fingerprint`，commit 创建后增加完整 `commit`。状态为 `committing -> pending -> completed`，不记录时间。
- commit 前写 `committing`；成功后写目标 commit 与 `pending`；确认远端目标分支包含该 commit 才写 `completed`。显式按记录中的 remote/ref 推送，不 force，不附带其他分支或发布动作。无 upstream 或 detached HEAD 时停止，先由用户配置目标。
- 中断在 commit 后、pending 写回前：只在 HEAD 的父提交等于 base_head、提交消息匹配且代码快照一致时认定为该次 commit；无法确定则停止。commit 尚未发生时重新运行 CI 和提交前门禁。
- pending 恢复先核对分支、推送目标、HEAD 和代码快照，直接补推原 commit，不再创建重复 commit；completed 恢复也确认远端包含该 commit。远端已继续前进时通过实际远端祖先关系确认，不能只用本地 upstream 缓存。
- 工作区干净且无本 session 记录时，也核对并推送当前 HEAD；只有远端确认后才成功，不以“无 diff”替代推送结果。
- 记录后代码或目标改变时停止；主会话重新验证、重新验收后才能启动新 session，旧记录保留供复核。远端不可达、拒绝推送或无法确认时返回失败，保留本地 commit。
