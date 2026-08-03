# 后端开发规范

Backend 主规范。它定义插件级稳定约束；目标项目的真实架构、模块名称、依赖版本、包职责和目录职责以目标项目代码与 `docs/`、`.ai/` 产物为准。

## 1. 文档定位

本页保留：
- backend 模块、包边界与依赖方向的确认方法
- 日常编码必须遵守的稳定工程约束
- Controller、错误处理、响应契约和 OpenAPI 的默认写法
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

### 2.1 构建与模块职责

先读取目标项目的 `backend/pom.xml`、`README.md`、`docs/` 与 `.ai/design/`，确认实际模块职责。不要把历史项目中的 `api/`、`domain/`、`application/`、`infrastructure/`、`test-support/` 等名称当作默认结构。

### 2.2 依赖方向

- 共享业务核心不应反向依赖上层 Web/Controller 逻辑。
- Web/API 模块负责对外 HTTP 暴露、参数绑定、认证入口、错误转换与路由装配，可依赖业务核心。
- 应用启动模块负责进程启动、配置装配、迁移触发和运行期集成。
- 运行期配置与依赖真相以目标项目构建文件、`application*.yml`/`properties` 和源码为准。

### 2.3 当前技术基线

- Java + Spring Boot 是默认后端技术方向。
- Web 框架默认按 Spring MVC 处理；若目标项目使用 WebFlux，以目标项目现有模式为准。
- ORM、SQL toolkit、迁移工具、错误库和日志库以目标项目实际依赖为准。常见组合是 Spring Data JPA/MyBatis/jOOQ、Flyway/Liquibase、SLF4J + Logback。
- 若目标项目使用 OpenAPI，优先沿用项目当前 OpenAPI 工具链；默认模板使用 `springdoc-openapi`，规范入口为 `/v3/api-docs`。

## 3. 稳定工程约束

### 3.1 Spring 组件与依赖注入

- 默认使用构造函数注入，依赖字段保持 `final`，不要新增字段注入。
- `@RestController` 负责 HTTP 参数绑定、权限入口和错误转换，复杂业务逻辑下沉到 service、use case 或相邻业务模块。
- `@Service` 承载业务编排和事务边界；`@Repository` 或数据访问适配器承载持久化细节。
- `@Transactional` 放在实际业务事务边界上，不为只读字段映射或 DTO 转换增加事务。
- 抽象设计优先服从当前模块边界和测试替身需求，不为套模板而新增接口层。

### 3.2 类型、错误与 ID

- 共享业务语义优先使用明确的 Java 类型、record、enum 或 value object 表达，不传递松散字符串协议。
- 跨模块共享的协议类型优先放在目标项目已有的共享业务模块。
- 共享错误优先使用项目内稳定异常/错误类型，不向客户端直接暴露底层异常对象。
- 新增业务 ID 必须沿用目标项目已有 ID 策略；没有明确策略时，先在设计文档中定下来，不在实现中临时混用。
- 不使用空 `catch`、吞异常或把业务失败统一包装成不透明 `RuntimeException`。
- 不在普通业务路径返回 `null` 表示失败；按项目既有风格使用异常、`Optional` 或结果类型。

### 3.3 HTTP 与 OpenAPI

- 普通业务 REST 接口优先返回稳定 JSON DTO，不直接暴露 JPA Entity、数据库模型或内部聚合。
- 普通业务 REST 接口新增或重构时，优先向统一错误/响应模型收敛：
  - 成功优先使用项目已有的统一响应包装或明确 DTO
  - 失败优先经 `@ControllerAdvice`、`ProblemDetail` 或项目统一错误模型输出
- 协议型、回调型、重定向、webhook、透传和 API-key 外部集成接口属于显式例外，不强制包成统一成功响应，但必须在模块内保持一致。
- 删除类接口优先使用 `204 No Content`；创建类接口只有真实返回创建语义时才使用 `201 Created`。
- 新增或修改接口时，同步维护 springdoc/OpenAPI 注解或确保自动生成的 `/v3/api-docs` 与真实接口一致。
- `@Operation`、`@ApiResponse`、`@Parameter`、`@Schema` 中的状态码、body、路径参数和真实运行时返回必须一致。
- 需要认证的接口，文档说明、401/403 响应和真实权限判断必须一致。
- 对外接口的错误响应应可稳定消费；如果接口属于协议例外，文档必须按真实协议声明，而不是伪装成普通业务响应。

### 3.4 数据访问与日志

- 数据访问优先服从当前模块事实，不强制把所有逻辑改写成统一模板分层。
- 数据库变更通过 Flyway、Liquibase 或项目既有迁移机制维护，不在文档中定义第二套手工流程。
- 日志统一使用项目现有 SLF4J 门面，记录动作、关键上下文和失败原因，不泄露敏感信息。

### 3.5 新代码默认写法

- 新增功能时，先复用当前模块已有风格；如果该模块风格明显分裂，优先采用本规范中较新的收敛方向，而不是复制更旧的写法。
- 新增普通 REST Controller 时，优先选择明确的返回 DTO 或 `ResponseEntity<T>`，不要用 `Object` 隐藏契约。
- 新增 DTO 时，请求和响应对象优先与领域对象/Entity 分离，避免 API 契约被内部模型绑死。
- 新增共享 Web 基础设施时，优先放在项目已有共享落点，不新建第二套重复抽象。
- 新增校验逻辑时，优先沿用目标项目现有 Bean Validation、业务校验和异常映射路径，不随意引入新的参数绑定范式。

## 4. 当前实现边界

以下内容不再视为 backend 主规范的默认事实或默认要求：

- 六边形架构的教学式模板代码
- 所有业务都必须按 Repository + Service + Policy 样板实现
- 大段 RBAC、分页、配置管理和日志教程
- 用长示例代替仓库真实实现边界
- 为了“统一风格”而进行的大规模目录搬迁
- 强制所有接口都套同一种响应包装

如果未来某个 feature 需要更细的局部规则，应写到该 feature 的设计文档、测试文档或 agent 验收文档，而不是回灌到 backend 主规范。

## 5. 完成前最低验证

```bash
cd backend
mvn test
```

说明：
- 上述顺序用于 backend 代码质量收口；优先使用目标项目已有 wrapper。
- 若项目在 `pom.xml` 中定义了格式化或静态检查插件，按 `${CLAUDE_PLUGIN_ROOT}/guides/backend/validation.md` 升级执行；本插件不要求新增这些依赖。
- 后端测试执行与补测证据属于 backend/test、backend-accept 或显式测试命令。
- OpenAPI 导出与前端 API 生成验收属于 backend-accept。

如需更完整门禁、环境启动和 OpenAPI 一致性检查，按 `${CLAUDE_PLUGIN_ROOT}/guides/backend/validation.md` 与 `${CLAUDE_PLUGIN_ROOT}/guides/backend/quality.md` 执行。
