---
name: t-demo-accept
description: >
  Demo 测试验收命令。验证 Playwright E2E 测试与用户故事一致性、可执行性和代码质量。
argument-hint: [测试文件路径|角色名|all]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
---

# Demo 测试验收

运行时边界统一参考：`protocols/runtime-boundaries.md`

## 目标
- 验证测试是否覆盖用户故事。
- 验证测试是否可编译、可运行且全部通过。
- 输出结构化验收报告到 `.ai/quality/`。

## 参数
```bash
/t-demo-accept [target]
```

`target` 说明：
- 测试文件路径：`demo/e2e/super-admin/super-admin-comprehensive-demo.e2e.ts`
- 角色名：`super-admin` / `realm-admin` / `regular-user` / `third-party-app`
- `all` 或留空：验收全部 Demo 测试

## 执行流程
1. 识别目标测试文件。
- 若是文件路径：仅处理该文件。
- 若是角色名：匹配 `demo/e2e/**` 下对应文件。
- 若是 `all` 或空：扫描 `demo/e2e/**/*.e2e.ts`，排除 `fixtures/`、`templates/`、`verification/`。

2. 用户故事一致性检查（必须）。
- 读取测试文件顶部注释中的用户故事路径。
- 校验用户故事文件存在。
- 核对场景覆盖、角色匹配、关键断言与验收标准。

3. 编译检查（必须）。
```bash
cd demo && npm run build
```

4. 测试执行检查（必须）。
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py "[测试文件]" --mode fast --log-level mini
```
- 若任一测试失败、超时或编译失败，直接判定该文件 `REJECTED`。

5. 代码质量检查。
```bash
grep -n "verifyTestEnvironment\|cleanupDemoTestData" [测试文件路径]
grep -n "UnifiedLogger\|logger\." [测试文件路径]
grep -n "waitForTimeout" [测试文件路径]
grep -n "data-testid\|getByRole\|getByText" [测试文件路径]
wc -l [测试文件路径]
```

6. 生成报告。
- 单文件：`.ai/quality/demo-accept-[name]-[YYYYMMDD-HHMMSS].md`
- 批量：同时生成汇总 `.ai/quality/demo-accept-summary-[YYYYMMDD-HHMMSS].md`

## 输出格式
每个文件产出：
- 状态：`ACCEPTED` / `ACCEPTED_WITH_IMPROVEMENTS` / `REJECTED`
- 分数：0-100
- 问题清单：P0 / P1 / P2
- 证据：失败命令、日志路径、相关代码位置

日志路径统一使用仓库相对路径：
- `log/backend-demo.log`
- `log/frontend-demo.log`
- `demo/test-results/`

## 失败处理
- 用户故事不存在：直接拒绝验收。
- 编译失败：直接拒绝验收。
- 测试失败或超时：直接拒绝验收。
- 批量模式下：记录失败并继续处理后续文件。

## 质量门禁
P0 必须全部通过：
- 用户故事映射有效
- 编译成功
- 测试全部通过
- 存在环境验证与数据清理
- 使用 UnifiedLogger

允许 `ACCEPTED_WITH_IMPROVEMENTS` 的前提：
- 所有测试通过
- 无 P0 问题

## 相关引用
- `agents/demo-accept.md`
- `agents/demo-dev.md`
- `agents/demo-diagnose.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/index.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/pom-guide.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/selector-strategy.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/test-maintenance.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/e2e-testing.md`
