# Demo 测试调试指南（Agent 主规范）

**定位**：本文件统一后端与前端的 Demo 失败排查流程。
**适用对象**：backend-dev、frontend-dev、demo-dev。

## 日志文件位置

- 控制台日志：`demo/test-results/console-logs/[测试名称]-[时间戳].log`
- 日志摘要：`demo/test-results/console-logs/*-summary.json`
- 后端日志：`log/backend-demo.log`
- 前端日志：`log/frontend-demo.log`
- 测试产物：`demo/test-results/artifacts/`

## 常用查看命令

```bash
# 最新控制台日志
cat demo/test-results/console-logs/$(ls -t demo/test-results/console-logs/*.log | head -1)

# 日志摘要
cat demo/test-results/console-logs/*-summary.json | jq

# 最近 100 行服务日志
tail -100 log/backend-demo.log
tail -100 log/frontend-demo.log

# 实时追踪
tail -f log/backend-demo.log
tail -f log/frontend-demo.log
```

## 快速分诊

### 1. 控制台日志有前端错误

- 归类：前端问题
- 检查：组件渲染、状态管理、API 调用、表单校验
- 处理：frontend-dev 修复，必要时联动 backend-dev

### 2. 后端日志有异常

- 归类：后端问题
- 检查：错误堆栈、请求参数、权限和数据状态
- 处理：backend-dev 修复并回归测试

### 3. 无明显错误但测试失败

- 归类：测试稳定性问题
- 检查：网络请求、超时、竞态、选择器唯一性
- 处理：优化等待与断言策略、修复选择器

## Fixture 与日志约定

- 推荐通过 `demo/e2e/fixtures/demo-page.fixtures.ts` 接入 `demoLogger`、`testStartTime` 和 `cleanupTestData()`。
- `demoLogger` 由 fixture 自动收尾；排障时不要要求在测试里手动调用 `logger.finalize()`。
- 如日志行为与预期不符，优先检查 fixture 是否被绕过、`beforeEach/afterEach` 是否仍走统一入口。

## 高频问题样例

### UUID 类型转换错误

**症状**：`column "id" cannot be cast to type uuid`

```sql
-- 查询中使用 ::text 转换
WHERE id = $1::text
```

```rust
.use_query(&[&id.to_string()])
```

### Async 错误处理不当

```rust
// 错误
let result = some_async_function().unwrap();

// 正确
let result = some_async_function().await?;
```

### 前端表单/网络请求失败

- 检查 Zod schema 与字段绑定
- 校验 API 路径与认证信息
- 核对请求/响应格式与权限配置

## 日志分析技巧

```bash
# 查找错误关键词
grep -i "error" log/backend-demo.log
grep -i "error" log/frontend-demo.log

# 查找最近错误
tail -1000 log/backend-demo.log | grep -i "error"
tail -1000 log/frontend-demo.log | grep -i "error"

# 控制台日志中查找失败请求
grep "FAILED" demo/test-results/console-logs/*.log
```

## 与诊断 Agent 协作

复杂失败优先走 demo-diagnose：
1. 读取统一日志并分类
2. 生成诊断报告
3. 路由给 frontend-dev / backend-dev 修复

## 提交前预防性检查

```bash
# Backend
cd backend && cargo check --package <api-package>
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- --package <core-package> --lib

# Frontend
cd frontend && npm run type-check
cd frontend && npm run build

# Demo
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py demo/e2e/ --mode fast
```

其中 `<api-package>` 和 `<core-package>` 应替换为目标仓库实际的 backend crate/package 名称。
