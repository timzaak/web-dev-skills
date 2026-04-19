# TDD 工作流程详细指南

本文档提供 Test-Driven Development（TDD）的完整示例和详细说明。

## Domain 层开发：采用 TDD 模式

**适用场景**：
- 纯业务逻辑（如：密码策略、权限验证）
- 不依赖外部服务（数据库、HTTP、Redis）
- 核心算法和数据转换

**TDD 工作流程（Red-Green-Refactor）**：

```rust
// ========== Step 1: Red - 编写失败的测试 ==========
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_password_validation_too_short() {
        let policy = PasswordPolicy::new(8);
        let result = policy.validate("abc123");  // 只有 6 个字符
        assert!(result.is_err());
        assert!(matches!(result, Err(ValidationError::TooShort)));
    }

    #[test]
    fn test_password_validation_missing_uppercase() {
        let policy = PasswordPolicy::new(8);
        let result = policy.validate("abcdefgh123");
        assert!(result.is_err());
        assert!(matches!(result, Err(ValidationError::MissingUppercase)));
    }

    #[test]
    fn test_password_validation_success() {
        let policy = PasswordPolicy::new(8);
        let result = policy.validate("Abc12345");
        assert!(result.is_ok());
    }
}

// ========== Step 2: Green - 实现最小可行代码 ==========
impl PasswordPolicy {
    pub fn new(min_length: usize) -> Self {
        Self { min_length }
    }

    pub fn validate(&self, password: &str) -> Result<(), ValidationError> {
        if password.len() < self.min_length {
            return Err(ValidationError::TooShort);
        }
        if !password.chars().any(|c| c.is_uppercase()) {
            return Err(ValidationError::MissingUppercase);
        }
        Ok(())
    }
}

// ========== Step 3: Refactor - 重构优化代码结构 ==========
// 提取辅助方法、优化逻辑、提升可读性
impl PasswordPolicy {
    fn has_uppercase(&self, password: &str) -> bool {
        password.chars().any(|c| c.is_uppercase())
    }

    fn has_digit(&self, password: &str) -> bool {
        password.chars().any(|c| c.is_ascii_digit())
    }
}
```

**快速反馈**：
```bash
# 只运行单元测试（秒级）
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- --package <core-package> --profile quick

# 只运行当前模块的测试
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- --package <core-package> -- domain::user::policy::tests
```

## Application 层开发：部分采用 TDD

**适用场景**：
- Service 层的业务编排逻辑
- 可以使用 mockall Mock Repository 依赖

**示例**：
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;

    #[tokio::test]
    async fn test_user_service_create_success() {
        // Given: Mock Repository
        let mut mock_repo = MockUserRepository::new();
        mock_repo.expect_find_by_email()
            .with(eq("test@example.com"))
            .returning(|_| Ok(None));

        mock_repo.expect_create()
            .returning(|_| Ok(User::fake()));

        // When: 调用 Service
        let service = UserServiceImpl::new(Arc::new(mock_repo));
        let result = service.create_user("test@example.com", "Pass123").await;

        // Then: 验证结果
        assert!(result.is_ok());
    }
}
```

## TDD 最佳实践

1. **编写最小测试**：从一个最简单的测试开始
2. **测试驱动实现**：只写足够的代码让测试通过
3. **重构优化**：测试通过后重构代码结构
4. **频繁运行测试**：每次修改后立即运行测试验证

## 参考资源

- [Rust Testing Guide](https://doc.rust-lang.org/book/ch11-00-testing.html)
- [mockall Documentation](https://docs.rs/mockall/latest/mockall/)
- [TDD Best Practices](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
