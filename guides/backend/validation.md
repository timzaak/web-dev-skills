# 编译验证步骤

⚠️ **CRITICAL**: 在标记任务为"完成"之前，**必须**执行以下验证。

## 验证清单

### 1. 编译/测试验证（MANDATORY）

后端测试统一入口是 `uv run scripts/backend-test.py`：它负责测试容器环境（PostgreSQL/Redis）、必要环境变量注入和测试代码 DDL guard。不要用裸 `mvn test` 替代，否则会缺失环境与 guard，产生不可靠结果。

```bash
uv run scripts/backend-test.py --
```

**验收标准**：
- ✅ 编译成功（**0 errors**）
- ✅ 测试执行成功（**0 failed**）
- ⚠️ 警告可以接受，但必须记录

**如果编译或测试失败**：
- 分析错误原因（import 错误、Bean 装配错误、类型错误、测试断言失败等）
- **立即修复阻塞错误**
- 重新验证同一命令
- 最多重试 3 次
- **仍然失败**：❌ 不能标记任务为"完成"

**重要**：
- 编译错误必须在完成前修复
- 不能将"编译有错误"的任务标记为"完成"
- 这是任务完成的**必要条件**，不是可选步骤
- 需要收敛到更窄范围时，用 `--module <module>` 或 `--tests '*<TestClass>'`；模块名取自 `backend/<dir>/pom.xml` 的 `<artifactId>`

### 2. 最终收口（backend accept 后必须执行）

```bash
/code-review
cd backend && mvn test
cd backend && mvn verify
```

规则：
- 这一步对应 `/t-backend-finalize [feature]`。
- 后端静态质量检查使用 Java/Spring 项目的 Maven 命令；非 Java 后端工具链命令不适用于本插件后端。
- 若项目在 `pom.xml` 中定义了格式化或静态检查插件，按项目已有 Maven goal 执行；本插件不要求新增这些依赖。
- 后端测试执行与补测证据属于 backend/test、backend-accept 或显式测试命令。
- 同一 feature 再次执行时，默认从失败步骤恢复，无需额外参数。

### 3. 格式化检查（可选但推荐）

按项目现有工具执行，不新增第二套格式化方案：

```bash
cd backend && mvn spotless:check
```

如果项目提供自动修复任务，可在收口阶段运行：

```bash
cd backend && mvn spotless:apply
```

### 4. 受影响单元测试（backend-dev 新增/改动单测时 MANDATORY）

凡新增或改动了单元测试，交付前必须用统一入口跑通相关测试（收敛到最小范围，不要默认全量）：

```bash
uv run scripts/backend-test.py -- --tests '*<TestClass>'
```

`<TestClass>` 取目标仓库实际的 Java 测试类名。**禁止**用裸 `mvn test` 替代统一入口（会缺失测试环境与 DDL guard）。

## 任务完成定义

**只有在以下所有条件满足时，才能标记任务为"完成"**：
- ✅ 编译成功（**0 errors**）
- ✅ 代码格式正确（或已格式化）
- ✅ 核心功能测试通过（如果有相关测试）

**如果任何验证失败**：
- ❌ **不能**标记任务为"完成"
- 🔄 **必须**修复并重新验证
- 📝 在完成报告中记录修复过程

## 常见错误模式

- **Import 错误**：导入正确的 Spring MVC、validation、security 或 persistence 类型
- **Controller 签名**：参考现有 Controller 的 `@PathVariable`、`@RequestParam`、`@RequestBody`、`ResponseEntity` 写法
- **Bean 装配错误**：确认组件位于 Spring Boot 扫描包下，构造函数依赖有唯一 Bean
- **事务边界错误**：把 `@Transactional` 放在 service/use case 层，不放在 DTO 转换或 Controller 参数绑定上
- **校验未生效**：请求 DTO 使用 Bean Validation 注解，Controller 参数使用 `@Valid`
- **错误映射不一致**：业务异常通过项目统一 `@ControllerAdvice` 或错误模型输出

## 典型错误处理

### Controller 参数绑定示例

```java
// 错误：路径参数没有绑定注解
UserResponse getUser(UUID id) {
    return service.getUser(id);
}

// 正确：显式绑定路径参数
@GetMapping("/users/{id}")
UserResponse getUser(@PathVariable UUID id) {
    return service.getUser(id);
}
```

### 请求校验示例

```java
// 错误：DTO 有约束但 Controller 未触发校验
@PostMapping("/users")
UserResponse createUser(@RequestBody CreateUserRequest request) {
    return service.createUser(request);
}

// 正确：使用 @Valid 触发 Bean Validation
@PostMapping("/users")
UserResponse createUser(@Valid @RequestBody CreateUserRequest request) {
    return service.createUser(request);
}
```

### 错误处理示例

```java
// 错误：吞掉异常并返回 null
try {
    return repository.findById(id).orElse(null);
} catch (Exception ignored) {
    return null;
}

// 正确：表达业务失败，由统一异常映射转换 HTTP 响应
return repository.findById(id)
        .orElseThrow(() -> new UserNotFoundException(id));
```
