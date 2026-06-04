# 后端测试指南

适用于目标项目的 Rust 后端测试。

## 入口

推荐入口：

```bash
uv run scripts/backend-test.py
```

需要显式复用环境时：

```bash
uv run scripts/test-start.py
uv run scripts/backend-test.py
uv run scripts/test-stop.py
```

## 项目事实确认

- 后端 workspace 真相以 `backend/Cargo.toml` 为准。
- 测试隔离以目标项目现有 test helper、fixture、schema 或 database 隔离实现为准。
- 真实数据库结构只来自目标项目迁移目录。
- 路由断言、租户参数和鉴权前提以当前真实接口与设计文档为准。

## 编写规则

- 单元测试只覆盖高价值局部行为：业务规则、边界条件、状态转换、权限判断、错误映射、数据规范化、核心算法，以及场景测试难稳定覆盖但有回归风险的分支。
- 不为只做字段赋值的 struct `new()`/builder/getter/setter、DTO/derive-only 类型、常量、简单 enum、机械字段映射或第三方库保证行为编写单元测试。
- 允许不新增单元测试；若改动只是 DTO、路由注册、字段透传或 OpenAPI 注解，优先用编译、定向场景测试或 OpenAPI 生成验证覆盖。
- 场景测试覆盖跨模块流程、数据库交互和 HTTP 主链路。
- 场景测试统一优先复用测试上下文和统一测试路由入口。
- 不在测试代码里维护第二套 DDL；需要结构变更时先改 migration。
- 路由断言与示例应使用当前真实接口路径，不沿用历史项目中的旧路径。

## 验证

常用命令：

```bash
uv run scripts/backend-test.py
uv run scripts/backend-test.py -- test_scenario
uv run scripts/backend-test.py -- -R latest
```

后端测试统一使用 `uv run scripts/backend-test.py -- [filter]`。需要串行执行时，仍使用统一入口并传递 nextest 参数：`uv run scripts/backend-test.py -- --test-threads 1 [filter]`，同时说明串行原因（例如全局状态、端口、单例或非隔离外部资源）。`cargo run` 只适用于启动应用、导出 OpenAPI 等二进制入口，不作为测试入口。

格式与静态检查收口：

```bash
cd backend
/code-review
cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features
cargo fmt --all
```

## 参考

- 环境与测试总览：[`environment-and-testing-guide.md`](${CLAUDE_PLUGIN_ROOT}/guides/core/environment-and-testing-guide.md)
- 后端开发规范：[`development.md`](${CLAUDE_PLUGIN_ROOT}/guides/backend/development.md)
- Backend 验收：[`quality.md`](${CLAUDE_PLUGIN_ROOT}/guides/backend/quality.md)
