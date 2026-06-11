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
        "type": "architectural_violation|spring_component_boundary|type_safety|error_handling|code_simplicity",
        "description": "Human-readable description of the issue",
        "severity": "critical|high|medium|low",
        "location": "file:line if applicable"
      }
    ],
    "corrected_code": "```java\n// Complete corrected implementation\n```",
    "rationale": {
      "summary": "Brief summary of changes",
      "detailed_explanation": "Detailed explanation of why changes are needed",
      "architectural_compliance": "How changes ensure hexagonal architecture compliance",
      "best_practices_applied": ["List of Java Spring Boot best practices applied"]
    }
  }
}
```



### 检查清单

- **架构边界合规性**
   - Domain/业务核心不反向依赖 Web 层
   - Controller 只做 HTTP 绑定、权限入口和错误转换
   - Service/use case 承载业务编排与事务边界

- **Spring 组件使用正确性**
   - 默认使用构造函数注入，不新增字段注入
   - `@Transactional` 放在真实业务事务边界
   - Bean 位于组件扫描范围内，依赖唯一且明确

- **类型安全**
   - UUID/String/Long 等 ID 类型与项目策略一致
   - Optional 或空值处理符合项目约定
   - DTO、Entity、领域对象边界清晰

- **错误处理**
   - 避免吞异常和不透明 RuntimeException
   - 通过统一异常映射输出稳定错误响应
   - 提供有意义的错误上下文

- **代码简洁性**
   - 遵循质量规范
   - 避免重复代码
   - 函数职责单一
   - 嵌套层级不超过 3 层
- **权限**
   - 权限校验没问题   

## 校准流程

- 对照检查清单分析代码
- 识别所有违反规范的问题
- 生成修正后的代码
- 输出结构化报告

## 参考资源

- [Backend Development Guide](${CLAUDE_PLUGIN_ROOT}/guides/backend/development.md)
- [Backend Agent Guide](${CLAUDE_PLUGIN_ROOT}/agents/backend-dev.md)
