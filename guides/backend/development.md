# 后端开发规范

Backend 主规范。它定义插件级稳定约束；目标项目的真实架构、crate 名称、依赖版本和目录职责以目标项目代码与 `docs/`、`.ai/` 产物为准。

## 1. 文档定位

本页保留：
- backend crate 边界与依赖方向的确认方法
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
- 完成前验证：`${CLAUDE_PLUGIN_ROOT}/guides/backend/validation.md`
- 完整验收：`${CLAUDE_PLUGIN_ROOT}/guides/backend/quality.md`

## 2. 当前架构事实

### 2.1 Workspace 与 crate 职责

先读取目标项目的 `backend/Cargo.toml`、各 crate 的 `Cargo.toml`、`README.md`、`docs/` 与 `.ai/design/`，确认实际 crate 职责。不要把历史项目中的 `api/`、`domain-core/`、`app/`、`test-support/` 等名称当作默认结构。

### 2.2 依赖方向

- 共享业务核心不应反向依赖上层 HTTP 逻辑。
- HTTP/API crate 负责对外 HTTP 暴露与路由装配，可依赖业务核心。
- 应用启动 crate 负责进程启动、配置装配和迁移运行。
- 运行期配置与 workspace 级依赖真相以 `backend/Cargo.toml` 和各 crate 源码为准。

### 2.3 当前技术基线

- Rust + Tokio + Axum 是默认后端技术方向。
- ORM、SQL toolkit、迁移工具、错误库和日志库以目标项目实际依赖为准。
- 若目标项目使用 OpenAPI，优先沿用项目当前的 OpenAPI 工具链；默认模板使用 `utoipa`。

## 3. 稳定工程约束

### 3.1 异步与 trait

- 所有 I/O 必须使用 `async/await`。
- 默认不要重新引入 `async-trait`；优先沿用仓库现有的原生 async trait 写法。
- trait 设计优先服从当前 crate 边界和测试替身需求，不为套模板而新增抽象层。

### 3.2 类型、错误与 ID

- 共享业务语义优先使用结构体和枚举表达，不传递松散字符串协议。
- 跨 crate 共享的协议类型优先放在目标项目已有的共享业务核心 crate。
- 共享错误优先使用项目内稳定错误类型，不向客户端直接暴露底层错误对象。
- 新增 `domain-core/` 领域错误时，不要继续扩大对 HTTP 类型的依赖；HTTP 状态码和响应 body 优先在 `api/` 层处理。
- 新增 `api/` handler 时，不再新增 `(StatusCode, String)`、裸 `StatusCode` 错误或手写 `{"error": "..."}` 风格。
- 新增业务 ID 必须沿用目标项目已有 ID 策略；没有明确策略时，先在设计文档中定下来，不在实现中临时混用。
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
- 新增校验逻辑时，优先沿用目标项目现有校验路径，不随意引入新的 extractor 范式。

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
cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features
cargo fmt --all
```

说明：
- 上述顺序用于 backend 代码质量收口。
- 后端测试执行与补测证据属于 backend/test、backend-accept 或显式测试命令。
- OpenAPI 导出与前端 API 生成验收属于 backend-accept。

如需更完整门禁、环境启动和 OpenAPI 一致性检查，按 `${CLAUDE_PLUGIN_ROOT}/guides/backend/validation.md` 与 `${CLAUDE_PLUGIN_ROOT}/guides/backend/quality.md` 执行。
