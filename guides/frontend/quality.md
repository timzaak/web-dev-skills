# Frontend 验证与验收规范

完成任务前必须取得适用验证证据；`frontend-accept` 验收前读取 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md`，公共分级、结论、报告、只读边界和结构化输出只由该协议定义。设计适用性按 `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md`。

## 1. 完成前验证清单

在标记任务完成前必须执行（命令以目标项目 `frontend/package.json` 实际 scripts 为准）：

1. **类型检查（MANDATORY）**：`cd frontend && npm run type-check`（或 `npx tsc --noEmit`）—— 必须 0 errors；警告须记录；失败立即修复重跑（最多重试 3 次，仍失败不能标记完成）。
2. **构建验证（MANDATORY）**：`cd frontend && npm run build` —— 全部模块正确打包（最多重试 3 次）。
3. **代码质量检查（按项目配置）**：`cd frontend && npm run lint`（或 `npx eslint . --ext .ts,.tsx`）。
4. **定向测试**：`cd frontend && npm run test:run -- <受影响测试路径或 pattern>`（适用时）。

### 常见类型与表单排查要点

- **导入与 Props 类型**：对照库类型定义区分默认/命名导入；回调参数（如 `renderInput`）补齐显式类型（`React.ComponentProps<'input'>`），避免隐式 `any`。
- **API 生成类型**：使用 `@hey-api/openapi-ts` 等生成的客户端与类型，不手工复制请求/响应接口定义。
- **表单类型安全**：采用项目统一的 `useAppForm`、`getFieldErrorMessage` 与 `onSubmit`/`form.handleSubmit()`，避免 `any`、`as *FormData` 不安全断言以及在 `Subscribe` 之外直接读 `form.state.canSubmit`。

## 2. 只读验收依据（frontend-accept）

### 必要门禁

- 适用的类型检查、受影响测试和 lint 通过；构建/打包相关变更具备实际构建证据。
- 页面和交互符合设计及本轮验收目标，核对受影响的权限、错误、空/加载、表单校验与状态转换路径；样式变更按风险取得视觉证据。
- API 路径、方法、Query/Body/Path 参数、响应类型、错误结构和认证与当前服务契约一致；不把单租户等项目特定规则当作所有项目的默认事实。
- 本阶段负责的必要行为验证通过；后续 Demo 只有真实承接位置才可延期，未执行项不计为通过，最终承接阶段必须收口。

有 `any`、断言、复杂组件或重复逻辑时检查具体后果：导致校验、权限或交互错误的缺陷阻断；无具体行为影响的类型/结构整理列维护性改进，不以“零 any”或固定重复率代替判断。

### API 一致性与派生物边界

API 改动或生成物可能漂移时，优先核查上游 OpenAPI/生成证据并比对实际调用。需要补跑 `npm run generate-api` 等命令时，遵循公共协议的受版本控制派生物边界：核对输出范围与执行前后差异，并验证受影响消费者，不能手工改生成物取得通过。重复代码检查按公共协议执行。

### Demo-first

Demo 已覆盖的完整故事不重复新增同路径集成测试；局部测试须补明确的重要覆盖缺口。验收仍独立核查关键断言和实际行为证据，不能把“计划有 Demo”当作本阶段必要门禁通过。需要补验本阶段负责的 Demo 时使用项目实际 `scripts/web-demo-test-runner.py` 入口；已明确交给后续阶段的场景记录承接位置，不能提前宣称业务验收完成。
