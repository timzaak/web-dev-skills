# Calibration Mode 代码校准规范

## 模式触发条件

**触发**: prompt 中包含 "模式: CALIBRATION" 或 "CALIBRATION"

## 模式定义

**任务**: 检查代码示例质量，返回修正建议，不修改文件

## 不执行的操作

- 不修改任何文件
- 不编写测试
- 不运行编译检查

## 输出格式规范

```json
{
  "calibration_report": {
    "original_code_issues": [
      {
        "type": "architectural_violation|async_pattern|type_safety|error_handling|code_simplicity",
        "description": "Human-readable description of the issue",
        "severity": "critical|high|medium|low",
        "location": "file:line if applicable"
      }
    ],
    "corrected_code": "```rust\n// Complete corrected implementation\n```",
    "rationale": {
      "summary": "Brief summary of changes",
      "detailed_explanation": "Detailed explanation of why changes are needed",
      "architectural_compliance": "How changes ensure hexagonal architecture compliance",
      "best_practices_applied": ["List of Rust best practices applied"]
    }
  }
}
```



### 检查清单

1. **六边形架构合规性**
   - Domain 层无外部依赖
   - Application 层使用泛型依赖注入
   - Infrastructure 层正确实现适配器接口

2. **异步模式正确性**
   - 正确使用 async/await
   - 无阻塞调用（如 `std::thread::sleep`）
   - Tokio 运行时正确配置

3. **类型安全**
   - UUID vs String 正确使用
   - Option 处理避免 unwrap
   - Result 错误类型匹配

4. **错误处理**
   - 使用 `?` 传播错误
   - 避免 `.unwrap()` 和 `.expect()`
   - 提供有意义的错误上下文

5. **代码简洁性**
   - 遵循质量规范
   - 避免重复代码
   - 函数职责单一
   - 嵌套层级不超过 3 层
6. **权限**
   - 权限校验没问题   

## 校准流程

2. 对照检查清单分析代码
3. 识别所有违反规范的问题
4. 生成修正后的代码
5. 输出结构化报告

## 参考资源

- [Backend Development Guide](/guides/backend/development.md)
- [Backend Agent Guide](/agents/backend-dev.md)
