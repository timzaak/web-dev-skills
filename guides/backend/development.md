# 后端开发规范

当前 backend 的主规范。既说明当前仓库后端是怎么组织的，也说明新增或重构代码时必须遵守哪些稳定约束。

## 1. 文档定位

本页保留：
- 当前 backend 的 crate 边界与依赖方向
- 日常编码必须遵守的稳定工程约束
- handler、错误处理、响应契约和 OpenAPI 的默认写法
- 完成前最低验证命令

本页不展开：
- 测试环境启动细节与场景测试写法
- DDD 任务拆解、执行门禁与验收流程
- 大篇幅教学式模板、长示例和局部 recipe

相关入口：
- 测试规则：`./testing.md`
- backend 规范入口：`./index.md`
- 完成前验证：`../agents/backend/validation.md`
- 完整验收：`../agents/backend/quality.md`
- 错误与响应收敛规划：`../../.ai/future/error_refactor.md`

## 2. 当前架构事实

### 2.1 Workspace 与 crate 职责

| crate | 当前职责 |
| --- | --- |
| `api/` | HTTP 路由、handler、DTO、OpenAPI 暴露 |
| `domain-core/` | 共享领域模型、业务逻辑、错误类型、基础设施实现 |
| `app/` | 服务启动与迁移入口 |
| `test-db/` | 测试数据库隔离工具 |
| `test-support/` | 测试上下文、fixtures 与辅助函数 |
| `integration-tests/` | 集成测试 |

### 2.2 依赖方向

- `domain-core/` 是共享业务核心，不应反向依赖上层 HTTP 逻辑。
- `api/` 负责对外 HTTP 暴露与路由装配，可依赖 `domain-core/`。
- `app/` 负责进程启动、配置装配和迁移运行。
- 运行期配置与 workspace 级依赖真相以 `backend/Cargo.toml` 和各 crate 源码为准。

### 2.3 当前技术基线

- Rust 2021 edition
- Tokio 异步运行时
- Axum 0.8
- SeaORM 与 SQLx
- `utoipa` + Swagger UI
- `tracing`
- `thiserror` 与 `anyhow`

## 3. 稳定工程约束

### 3.1 异步与 trait

- 所有 I/O 必须使用 `async/await`。
- 默认不要重新引入 `async-trait`；优先沿用仓库现有的原生 async trait 写法。
- trait 设计优先服从当前 crate 边界和测试替身需求，不为套模板而新增抽象层。

### 3.2 类型、错误与 ID

- 共享业务语义优先使用结构体和枚举表达，不传递松散字符串协议。
- 跨 crate 共享的协议类型优先放在 `domain-core/`。
- 共享错误优先使用项目内稳定错误类型，不向客户端直接暴露底层错误对象。
- 新增 `domain-core/` 领域错误时，不要继续扩大对 HTTP 类型的依赖；HTTP 状态码和响应 body 优先在 `api/` 层处理。
- 新增 `api/` handler 时，不再新增 `(StatusCode, String)`、裸 `StatusCode` 错误或手写 `{"error": "..."}` 风格。
- 新增业务 ID 默认继续遵循 UUID v7 约束；不要回退到 UUID v4。
- 不使用 `unwrap()` 处理业务路径和 I/O 错误。

### 3.3 HTTP 与 OpenAPI

- Handler 负责参数提取、权限入口和 HTTP 错误转换，复杂业务逻辑下沉到 `core/` 或相邻业务模块。
- 普通业务 REST 接口优先返回稳定 JSON DTO，不直接暴露领域实体或数据库模型。
- 普通业务 REST 接口新增或重构时，优先向统一错误/响应模型收敛：
  - 成功优先使用统一响应包装
  - 失败优先收敛到 `api/` 层统一错误类型
- 协议型、回调型、重定向、webhook、透传和 API-key 外部集成接口属于显式例外，不强制包成统一成功响应，但必须在模块内保持一致。
- 删除类接口优先使用 `204 No Content`；创建类接口只有真实返回创建语义时才使用 `201 Created`。
- 新增或修改接口时，同步维护 `#[utoipa::path]` 注解。
- `#[utoipa::path]` 中的状态码、body 和真实运行时返回必须一致，不能出现文档写 `201`、代码实际返回 `200` 的情况。
- OpenAPI 路径参数命名应与当前真实接口保持一致，不延续旧项目的租户参数约束。
- 需要认证的接口，文档说明、403 响应和真实权限判断必须一致。
- 对外接口的错误响应应可稳定消费；如果接口属于协议例外，文档必须按真实协议声明，而不是伪装成普通业务响应。

### 3.4 数据访问与日志

- 数据访问优先服从当前模块事实，不强制把所有逻辑改写成统一模板分层。
- 数据库变更通过迁移文件维护，不在文档中定义第二套手工流程。
- 日志统一使用 `tracing`，记录动作、关键上下文和失败原因，不泄露敏感信息。

### 3.5 新代码默认写法

- 新增功能时，先复用当前模块已有风格；如果该模块风格明显分裂，优先采用本规范中较新的收敛方向，而不是复制更旧的写法。
- 新增普通 REST handler 时，优先选择明确的返回类型，不用 `impl IntoResponse` 隐藏契约，除非接口本身就是协议例外。
- 新增 DTO 时，请求和响应对象优先与领域对象分离，避免 API 契约被内部模型绑死。
- 新增共享 HTTP 基础设施时，优先放在 `api` 层已有共享落点，不新建第二套重复抽象。
- 新增校验逻辑时，优先沿用当前 `axum-valid` 和现有校验路径，不随意引入新的 extractor 范式。

## 4. 当前实现边界

以下内容不再视为 backend 主规范的默认事实或默认要求：

- 六边形架构的教学式模板代码
- 所有业务都必须按 Repository + Service + Policy 泛型样板实现
- 大段 RBAC、分页、配置管理和日志教程
- 用长示例代替仓库真实实现边界
- 为了“统一风格”而进行的大规模目录搬迁
- 强制所有接口都套同一种响应包装

如果未来某个 feature 需要更细的局部规则，应写到该 feature 的设计文档、测试文档或 agent 验收文档，而不是回灌到 backend 主规范。

## 5. 完成前最低验证

```bash
cd backend
/simplify
cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features
cargo fmt --all
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py
```

说明：
- 上述顺序用于 backend `accept` 通过后的统一收口，不替代 `backend-test` 的定向测试闭环。
- 在任务流中，这一步由 `/t-backend-finalize [feature]` 负责，默认从失败步骤恢复。

如需更完整门禁、环境启动和 OpenAPI 一致性检查，按 `../agents/backend/validation.md` 与 `../agents/backend/quality.md` 执行。
