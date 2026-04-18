# 后端测试指南

适用于当前仓库的 Rust 后端测试。

## 入口

推荐入口：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py
```

需要显式复用环境时：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/test-start.py
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/test-stop.py
```

## 当前事实

- 后端 workspace 真相以 `backend/Cargo.toml` 为准。
- 测试隔离以 `test-db/`、`test-support/` 和 schema 隔离实现为准。
- 真实数据库结构只来自 `backend/app/migrations/`。
- 单租户是当前默认前提，后端测试示例不再使用租户路径参数。

## 编写规则

- 单元测试覆盖纯逻辑和局部行为。
- 场景测试覆盖跨模块流程、数据库交互和 HTTP 主链路。
- 场景测试统一优先复用测试上下文和统一测试路由入口。
- 不在测试代码里维护第二套 DDL；需要结构变更时先改 migration。
- 路由断言与示例应使用当前真实接口路径，例如 `/api/auth/login`，而不是旧的租户前缀接口。

## 验证

常用命令：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- test_scenario
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -R latest
```

最终收口：

```bash
cd backend
/simplify
cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features
cargo fmt --all
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py
```

## 参考

- 环境与测试总览：[`environment-and-testing-guide.md`](${CLAUDE_PLUGIN_ROOT}/guides/core/environment-and-testing-guide.md)
- 后端开发规范：[`development.md`](${CLAUDE_PLUGIN_ROOT}/guides/backend/development.md)
- Backend 验收：[`quality.md`](${CLAUDE_PLUGIN_ROOT}/guides/backend/quality.md)
