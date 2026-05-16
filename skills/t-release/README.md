# t-release / 版本发布

Bump project version, create git tag, and push release commit to remote.

更新项目版本号、创建 git commit 和 tag、推送到远程。

## Usage / 用法

```bash
/t-release [版本号]
```

- 语义化版本号，如 `0.2.0`、`1.0.0`
- 最终 tag 必须是纯版本号，例如 `0.2.0`；输入 `v0.2.0` 会按 `0.2.0` 发布
- 留空时基于最新 semver tag 推荐下一版本号

## Preconditions / 前置条件

- 当前分支为 `main`
- 工作区干净（无未提交变更）
- 远程可访问
- 目标 tag 不存在，且对应的 `v<版本号>` tag 也不存在

## Updated Files / 更新文件

| File / 文件 | Field / 字段 | Note / 说明 |
|---|---|---|
| `backend/Cargo.toml` | `version` under `[workspace.package]` | Rust workspace |
| `frontend/package.json` | `"version"` | Frontend |
| `demo/package.json` | `"version"` | Demo tests |

`Cargo.lock` is auto-updated by `cargo check`.

## Flow / 执行流程

运行发布脚本：

```bash
python scripts/release.py [版本号]
```

脚本负责版本规范化、前置检查、版本文件更新、验证、commit、tag 和 push。不要手工拼接 release 命令。

## Error Handling / 失败处理

- 按脚本错误输出处理
- 验证失败时终止，不创建 commit/tag
- 推送失败时，本地 commit/tag 已保留，提示手动推送

## Examples / 示例

```bash
# 指定版本号
/t-release 0.2.0

# 交互式选择
/t-release
```

Expected output / 期望输出：

```
版本已更新到 0.2.0，commit abc1234 和 tag 0.2.0 已推送到远程。

修改的文件：
- backend/Cargo.toml — 0.1.1 → 0.2.0
- backend/Cargo.lock — 自动更新
- frontend/package.json — 0.1.1 → 0.2.0
- demo/package.json — 0.1.1 → 0.2.0
```
