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
- 健康检查通过（以目标项目健康检查契约为准）
- OpenAPI 关键注解完整（无阻塞缺失）
- OpenAPI 可成功导出，`frontend/api.json` 为有效 JSON
- 前端 API 客户端可成功生成

### P1（应通过）
- Clippy 无严重警告
- OpenAPI 注解完整（params/request_body/responses）
- ApiDoc 路径和 schema 注册完整

### P2（可改进）
- 复杂度和重复代码优化（重复代码检查结果必须写入 accept 报告）
- OpenAPI 描述信息增强

## 4. 执行步骤与命令

```bash
cargo build --workspace
uv run scripts/backend-test.py -- <targeted filter>
cat backend-test-output.log | grep -E "(error\[E|FAILED)" | head -20
npx jscpd --pattern "**/*.rs" --reporters console backend
```

规则：
- `backend-accept` 默认先做改动分析，再执行定向 `uv run scripts/backend-test.py -- <targeted filter>`；不得默认直接跑全量 `uv run scripts/backend-test.py --`。
- 只有在用户明确要求全量测试，或影响范围无法可靠收敛时，`backend-accept` 才允许升级到全量测试；一旦升级，则全量结果也必须通过。
- OpenAPI 导出与前端 API 生成属于 `backend-accept` 的 P0 验收项；失败时拒绝验收。
- 若 OpenAPI 导出或前端 API 生成失败，修复后至少重新执行受影响测试、OpenAPI 导出与前端 API 生成。

## 5. 环境验证（MANDATORY）

启动后端服务，然后进行健康检查（路径和响应结构以目标项目契约为准）：

```powershell
Start-Sleep -Seconds 5
$response = Invoke-WebRequest -Uri "http://localhost:<backend-port>/<health-path>" -UseBasicParsing
if ($response.StatusCode -ne 200) { exit 1 }
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
- `ACCEPTED`：P0/P1 全部通过
- `REJECTED`：任一 P0 失败
- `ACCEPTED_WITH_IMPROVEMENTS`：P0 全通过，存在 P1 或 P2 改进项

判定规则：
- 判定优先级为 `REJECTED` > `ACCEPTED_WITH_IMPROVEMENTS` > `ACCEPTED`。
- P1 失败不触发 `REJECTED`，但必须写入风险与修复建议。
- 只有 P0 失败才能触发 `REJECTED`。

### 报告最小字段
- 结论
- 门禁摘要
- P0/P1/P2 单行清单
- 证据路径
- Handoff

## 8. 禁止行为

- 禁止在编译或测试失败时给出“带改进通过”
- 禁止跳过环境验证
- 禁止跳过 OpenAPI 关键检查
- 每条结论必须给出文件位置证据
