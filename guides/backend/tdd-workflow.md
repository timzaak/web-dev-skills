# TDD 工作流程详细指南

本文档提供 Test-Driven Development（TDD）的完整示例和详细说明。

## Domain 层开发：采用 TDD 模式

**适用场景**：
- 纯业务逻辑（如：密码策略、权限验证）
- 不依赖外部服务（数据库、HTTP、Redis）
- 核心算法和数据转换

**不适用场景**：
- 只做字段赋值的 record/DTO/builder/getter/setter、常量和机械字段映射。

**TDD 工作流程（Red-Green-Refactor）**：

```java
// ========== Step 1: Red - 编写失败的测试 ==========
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class PasswordPolicyTest {

    @Test
    void rejectsPasswordWhenTooShort() {
        var policy = new PasswordPolicy(8);

        assertThatThrownBy(() -> policy.validate("abc123"))
                .isInstanceOf(ValidationException.class)
                .hasMessageContaining("too short");
    }

    @Test
    void rejectsPasswordWhenMissingUppercase() {
        var policy = new PasswordPolicy(8);

        assertThatThrownBy(() -> policy.validate("abcdefgh123"))
                .isInstanceOf(ValidationException.class)
                .hasMessageContaining("uppercase");
    }

    @Test
    void acceptsValidPassword() {
        var policy = new PasswordPolicy(8);

        assertThatCode(() -> policy.validate("Abc12345"))
                .doesNotThrowAnyException();
    }
}

// ========== Step 2: Green - 实现最小可行代码 ==========
final class PasswordPolicy {
    private final int minLength;

    PasswordPolicy(int minLength) {
        this.minLength = minLength;
    }

    void validate(String password) {
        if (password.length() < minLength) {
            throw new ValidationException("password is too short");
        }
        if (password.chars().noneMatch(Character::isUpperCase)) {
            throw new ValidationException("password must contain uppercase");
        }
    }
}

// ========== Step 3: Refactor - 重构优化代码结构 ==========
private boolean hasUppercase(String password) {
    return password.chars().anyMatch(Character::isUpperCase);
}
```

**快速反馈**（统一用 backend-test.py 入口，不要退回裸 `mvn test`）：

```bash
# 只运行当前测试类
uv run scripts/backend-test.py -- --tests '*PasswordPolicyTest'

# 只运行单个测试方法
uv run scripts/backend-test.py -- --tests '*PasswordPolicyTest.validateRejectsNoUppercase'
```

说明：上例测试的是 `validate` 的业务行为，不测试构造函数是否把字段赋值成功；只有构造函数包含校验、默认值合成或规范化时才测构造函数本身。

## Application 层开发：部分采用 TDD

**适用场景**：
- Service 层的业务编排逻辑
- 可以使用 Mockito 或项目既有 test double 隔离 Repository 依赖

**示例**：

```java
import static org.mockito.Mockito.when;

import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

class UserServiceTest {

    @Test
    void createsUserWhenEmailIsUnused() {
        var repository = Mockito.mock(UserRepository.class);
        when(repository.findByEmail("test@example.com")).thenReturn(Optional.empty());

        var service = new UserService(repository);

        service.createUser("test@example.com", "Pass123");

        Mockito.verify(repository).save(Mockito.any(User.class));
    }
}
```

## TDD 最佳实践

- **先判断测试价值**：只有能保护业务规则、边界、状态转换或错误语义时才写单元测试
- **测试驱动实现**：只写足够的代码让测试通过
- **重构优化**：测试通过后重构代码结构
- **频繁运行测试**：每次修改后立即运行测试验证

## 参考资源

- [Spring Boot Testing](https://docs.spring.io/spring-boot/reference/testing/)
- [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/)
- [Mockito Documentation](https://javadoc.io/doc/org.mockito/mockito-core/latest/org.mockito/org/mockito/Mockito.html)
