# Backend Agent 质量验收规范

## 1. 适用范围

适用于 `backend/` 代码变更的验收，包括：
- Rust 代码质量检查
- 测试执行与结果验证
- 服务环境可运行性验证
- OpenAPI 文档完整性检查

## 2. 前置检查（MANDATORY）

在执行验收前，先完成设计一致性检查：
- 参考 `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md` 的 DDD 总纲
- 读取 `.ai/design/[任务名].md`
- 豁免前缀：`bugfix-`、`refactor-`、`doc-`、`test-`、`style-`

## 3. 验收门禁

### P0（必须通过）
- 编译通过（0 errors）
- 受影响测试通过（0 failed）
- 环境可启动
- 健康检查通过（`/health` 返回 healthy，database/redis 均为 true）
- OpenAPI 关键注解完整（无阻塞缺失）

### P1（应通过）
- Clippy 无严重警告
- OpenAPI 注解完整（params/request_body/responses）
- ApiDoc 路径和 schema 注册完整

### P2（可改进）
- 复杂度和重复代码优化
- OpenAPI 描述信息增强

## 4. 执行步骤与命令

```bash
cargo build --workspace
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- <targeted filter>
cat backend-test-output.log | grep -E "(error\[E|FAILED)" | head -20
```

规则：
- `backend-accept` 默认先做改动分析，再执行定向 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- <targeted filter>`；不得默认直接跑全量 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py`。
- 只有在用户明确要求全量测试，或影响范围无法可靠收敛时，`backend-accept` 才允许升级到全量测试；一旦升级，则全量结果也必须通过。
- `backend-accept` 完成后，必须继续执行 backend finalize 收口。
- 收口入口固定为 `/t-backend-finalize [feature]`，`/simplify -> cargo clippy --fix -> cargo fmt --all -> 全量 uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py` 只属于该阶段，不应塞回 `backend-accept`。
- 若 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py` 在收口阶段失败，修复后至少重新执行 `cargo clippy --fix -> cargo fmt --all -> uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py`。

## 5. 环境验证（MANDATORY）

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/dev-start.py
```

健康检查（PowerShell 示例）：

```powershell
Start-Sleep -Seconds 5
$response = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing
if ($response.StatusCode -ne 200) { exit 1 }
```

预期响应：

```json
{
  "status": "healthy",
  "database": true,
  "redis": true
}
```

清理：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/dev-stop.py
```

规则：环境验证失败时，即使测试通过也必须拒绝验收。

## 6. OpenAPI 文档完整性检查

### 6.1 utoipa 注解
每个公开 HTTP handler 必须具备完整 `#[utoipa::path]`：
- HTTP 方法
- `path`（路径参数名称与真实接口保持一致）
- `tag`
- `params`（有路径/查询参数时）
- `request_body`（POST/PUT/PATCH）
- `responses`（成功与错误）

### 6.2 ToSchema
`#[utoipa::path]` 引用的请求/响应/错误类型必须 `derive(ToSchema)`。

### 6.3 ApiDoc 注册
检查 `backend/api/src/application/http/server/mod.rs`：
- `paths()` 覆盖所有端点
- `components(schemas())` 覆盖所有类型
- `tags()` 覆盖所有使用的 tag

### 6.4 生成验证

```bash
cd frontend && npm run generate-api
```

验证 `frontend/api.json`：
- JSON 有效
- path/schema/tag 完整
- 不包含与当前接口不一致的旧路径占位符

## 7. 报告与判定

输出文件：`.ai/quality/accept-[feature]-[date].md`

### 状态
- `ACCEPTED`：所有 P0/P1 通过
- `REJECTED`：任一 P0 失败
- `ACCEPTED WITH IMPROVEMENTS`：P0 全通过，存在 P2 改进项

### 报告最小字段
- 测试结果（总数/通过/失败）
- 构建与静态检查结果
- 环境验证结果
- OpenAPI 检查结果
- 阻塞问题与修复建议

## 8. 禁止行为

- 禁止在编译或测试失败时给出“带改进通过”
- 禁止跳过环境验证
- 禁止跳过 OpenAPI 关键检查
- 每条结论必须给出文件位置证据
