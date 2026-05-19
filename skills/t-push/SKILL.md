---
name: t-push
description: 根据 git diff 检测变更范围，仅运行受影响区域的 CI 检查，全部通过后 git commit && git push。
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
  - AskUserQuestion
---

# Push with Local CI

根据 `git diff --name-only` 检测变更范围，仅运行受影响区域的 CI 检查，全部通过后执行 git commit && git push。无需参数，commit message 从变更内容自动生成。

运行时边界统一参考：`protocols/runtime-boundaries.md`

## Fixed Flow

### 0. 前置检查
- 运行 `git status --short` 查看变更文件，确认有可提交的变更。若无变更，提示用户并停止。
- 运行 `git diff --name-only HEAD`（含未暂存）和 `git diff --name-only --cached`（已暂存）检测变更范围。

### 1. 检测变更区域
根据变更文件路径判断需要运行哪些检查：

| 文件路径前缀 | 触发的检查 |
|---|---|
| `backend/**` | Backend CI |
| `frontend/**` | Frontend CI |
| `demo/**` | Demo CI |

若无匹配（例如仅 `.md`、`docs/`、`scripts/` 或配置变更），跳过所有检查，直接进入 commit。

### 2. Backend CI（仅当 backend 有变更）
依次执行，任一失败则停止：

```bash
cd backend && cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features && cargo fmt --all
```

### 3. Frontend CI（仅当 frontend 有变更）
依次执行，任一失败则停止：

```bash
cd frontend && npm run lint && npm run format:check && npm run type-check && npm run test:run
```

如果目标项目 `package.json` 中没有 `format:check` 或 `test:run` 脚本，跳过对应步骤并继续。

### 4. Demo CI（仅当 demo 有变更）
依次执行，任一失败则停止：

```bash
cd demo && npm run lint && npm run type-check
```

### 5. Commit & Push
全部检查通过（或被跳过）后：

1. `git add -A`
2. 根据 `git diff --cached --stat` 自动生成简洁的 commit message，格式遵循项目惯例（如 `feat:`, `fix:`, `chore:`, `refactor:` 前缀）。
3. 展示生成的 commit message 给用户确认。
4. 用户确认后执行 `git commit -m "<message>"`。
5. `git push`

## Failure
- 任一 CI 步骤失败：**停止**，输出失败信息，不执行 commit/push。告知用户哪个步骤失败及错误摘要，由用户决定是否修复后重试。
- push 失败：输出错误信息，提示用户检查远程状态。

## Success Criteria
- 受影响区域的 CI 检查全部通过（或无受影响区域而跳过）。
- 代码已 commit 并 push 到远程。
