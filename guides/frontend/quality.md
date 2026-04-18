# Frontend Agent 质量验收规范

## 1. 适用范围

适用于 `frontend/` 代码变更的验收，包括：
- 类型安全与构建质量
- 前端测试与 lint
- 前后端 API 一致性
- Demo-first 测试策略合规

## 2. 前置检查（MANDATORY）

先完成设计一致性检查：
- 参考 `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md` 的 DDD 总纲
- 读取 `.ai/design/[任务名].md`
- 豁免前缀：`bugfix-`、`refactor-`、`doc-`、`test-`、`style-`

## 3. 验收门禁

### P0（必须通过）
- 类型检查通过（0 errors）
- 单元/集成测试通过（如有）
- Lint 无阻塞错误
- API 一致性无阻塞偏差（路径、方法、关键参数、关键响应）

### P1（应通过）
- 重复代码可控（建议 < 5%）
- 高复杂度组件可控
- 表单类型安全（零 `any`、零不安全断言）

### P2（可改进）
- 可维护性优化（拆分组件、提取 hooks）

## 4. 执行步骤与命令

```bash
cd frontend
npm run type-check
npm run test:run
npm run lint
npx jscpd src/
```

Demo 验证（仓库根目录）：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py demo/e2e/ --mode fast
```

## 5. API 一致性检查

导出方式：

```bash
cd frontend && npm run generate-api
```

检查项：
- 路径/方法一致
- 请求参数（Query/Body/Path）一致
- 响应字段与类型一致
- 错误码与错误结构一致
- 认证与当前单租户接口约束一致

## 6. Demo-first 测试策略

遵循“以 Demo 为主”策略：
- Demo 已覆盖功能，不应重复编写同类前端集成测试
- 保留的前端集成测试必须有明确不可替代用途
- 用户故事应可在 Demo 测试中映射验证

## 7. 报告与判定

输出文件：`.ai/quality/check-[date].md`

### 状态
- `ACCEPTED`：P0/P1 全部通过
- `REJECTED`：任一 P0 失败
- `ACCEPTED WITH IMPROVEMENTS`：P0 全通过，存在 P2 改进项

### 报告最小字段
- 类型检查、测试、lint 结果
- 重复代码/复杂度结果
- API 一致性差异清单
- 风险与修复建议（P0/P1/P2）

## 8. 禁止行为

- 未授权修改代码
- 只读验收默认禁止执行会改写仓库文件的命令
- 禁止无证据结论
