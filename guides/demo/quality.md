# Demo Agent 质量验收规范

## 1. 适用范围

适用于 `demo/e2e/**/*.e2e.ts` 的验收，包括：
- 用户故事一致性
- 编译与执行结果
- 测试代码质量
- 场景覆盖率与评分

## 2. 五阶段验收流程

### 阶段 1：用户故事一致性（MANDATORY）
- 测试文件必须映射到 `.ai/user-stories/*.md` 或 `docs/user-stories/*.md`
- `.ai/user-stories` 是发布前候选来源；验收报告必须标注 draft 来源，不得把它改写为已发布事实
- 场景、角色、断言与用户故事验收标准一致
- 场景覆盖率 < 50% 直接拒绝

### 阶段 2：测试编译验证（MANDATORY）

```bash
(cd demo && npm run build)
```

标准：0 TypeScript 编译错误。

### 阶段 3：测试执行验证（MANDATORY）

```bash
uv run scripts/demo-test-runner.py "${TEST_FILE}" --mode fast --log-level mini
```

标准：
- 0 failed
- 0 timeout
- 可定位日志文件

### 阶段 4：测试代码质量检查

P0：
- 使用 `verifyTestEnvironment()`
- 使用 `cleanupTestData()` 或等价封装完成清理
- 使用 `demoLogger` fixture
- 主验收断言不得依赖 `sonner`、toast、Snackbar 等自动消失提示
- 固定延迟 `waitForTimeout` 最小化

P1：
- 选择器优先语义化（`getByRole` / `getByLabel`）
- 复杂场景提供 `data-testid` 后备
- `waitForResponse` 使用 Promise 先注册后触发
- 自动消失提示仅可作为辅助断言，必须另有持久业务状态、页面状态、URL、列表/详情数据或稳定错误区域断言

P2：
- 文件和函数复杂度可控
- 重复代码可控（检查结果必须写入 accept 报告）

重复代码扫描命令：

```bash
npx jscpd --pattern "**/*.ts" --reporters console demo/e2e
```

### 阶段 5：覆盖率验证

覆盖率 = 已测场景 / 总场景 × 100%

阈值：
- >= 90%：优秀
- >= 70%：可接受
- < 70%：需补充

## 3. 评分与判定

总体评分：
- 用户故事一致性 20%
- 测试执行结果 30%
- 代码质量 30%
- 场景覆盖率 20%

状态阈值：
- 90-100：`ACCEPTED`
- 80-89：`ACCEPTED_WITH_IMPROVEMENTS`（仅在所有测试通过时允许）
- < 80：`REJECTED`

## 4. 拒绝条件

任一满足即 `REJECTED`：
- 用户故事文档不存在（`.ai/user-stories` 或 `docs/user-stories` 均未找到）
- 编译失败
- 任一测试失败或超时
- 缺失测试隔离（环境验证/数据清理）
- 缺失 `demoLogger` fixture
- 使用 `sonner`、toast、Snackbar 等自动消失提示作为主判断条件或唯一验收依据

## 5. 报告模板要求

输出文件：`.ai/quality/demo-accept-[feature]-[date].md`

最小字段：
- 结论
- 门禁摘要
- P0/P1/P2 单行清单
- 日志路径

批量验收需额外输出汇总报告：
- 总测试数
- ACCEPTED / ACCEPTED_WITH_IMPROVEMENTS / REJECTED 统计
- 失败测试单行清单

## 6. 禁止行为

- 禁止测试失败时标记“带改进通过”
- 禁止跳过用户故事一致性检查
- 禁止跳过执行验证
- 禁止降低标准让失败通过
