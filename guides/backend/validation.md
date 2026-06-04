# 编译验证步骤

⚠️ **CRITICAL**: 在标记任务为"完成"之前，**必须**执行以下验证。

## 验证清单

### 1. 编译/测试验证（MANDATORY）

优先使用目标项目 wrapper。

Maven：

```bash
cd backend && ./mvnw test
```

Gradle：

```bash
cd backend && ./gradlew test
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
- 若目标项目提供更窄的模块命令，应从 `backend/pom.xml`、`settings.gradle(.kts)`、现有脚本或 CI 配置确认真实模块名后执行

### 2. 最终收口（backend accept 后必须执行）

Maven：

```bash
/code-review
cd backend && ./mvnw test
cd backend && ./mvnw verify
```

Gradle：

```bash
/code-review
cd backend && ./gradlew test
cd backend && ./gradlew check
```

规则：
- 这一步对应 `/t-backend-finalize [feature]`。
- 若项目定义了 `spotlessApply`、`spotlessCheck`、`checkstyleMain`、`pmdMain` 或同类质量任务，按项目已有任务执行。
- 后端测试执行与补测证据属于 backend/test、backend-accept 或显式测试命令。
- 同一 feature 再次执行时，默认从失败步骤恢复，无需额外参数。

### 3. 格式化检查（可选但推荐）

按项目现有工具执行，不新增第二套格式化方案：

```bash
cd backend && ./mvnw spotless:check
cd backend && ./gradlew spotlessCheck
```

如果项目提供自动修复任务，可在收口阶段运行：

```bash
cd backend && ./mvnw spotless:apply
cd backend && ./gradlew spotlessApply
```

### 4. 快速测试（可选但推荐）

Maven：

```bash
cd backend && ./mvnw test -Dtest=<TestClassName>
```

Gradle：

```bash
cd backend && ./gradlew test --tests '*<TestClassName>'
```

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
