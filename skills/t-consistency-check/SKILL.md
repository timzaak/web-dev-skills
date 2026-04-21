---
name: t-consistency-check
argument-hint: [module-name|--all]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Task
  - Write
---

# 后端一致性检查

运行时边界统一参考：`protocols/runtime-boundaries.md`

## 目标
- 对比 PRD 与后端实现。
- 快速识别能力边界、模型约束、校验、权限、业务逻辑差异。
- 如发现接口说明或路由问题，单独记录，不要求回填 PRD 端点列表。
- 生成可跟踪的模块报告。

## 使用方式
```bash
/t-consistency-check realm
/t-consistency-check --all
```

## 执行流程
1. 解析参数。
- `--all`：扫描 `docs/prd/**/*.md` 自动提取模块名。
- 模块名：只检查指定模块。

2. 校验模块输入。
- `docs/prd/[module].md` 必须存在。
- 目标仓库中与 `[module]` 对应的后端领域实现目录必须存在；若未采用固定布局，先基于仓库真实结构定位模块代码。
- 目标仓库中与 `[module]` 对应的 HTTP/接口实现目录若不存在，记录为信息项而非直接失败。

3. 调用 `backend-consistency`。
```bash
Task: backend-consistency
prompt: 检查 [module] PRD 与后端实现一致性
```

4. 写入报告。
- 单模块：`.ai/quality/consistency-[module]-[YYYYMMDD-HHMMSS].md`
- 全量：额外生成 `.ai/quality/consistency-summary-[YYYYMMDD-HHMMSS].md`

## 报告要求
每个模块报告必须包含：
- 总分（0-100）
- API 能力边界 / 模型约束 / 校验 / 权限 / 业务逻辑分项
- 差异清单（P0/P1/P2）
- 具体文件定位与修复建议

### 差异判定（必检）
- PRD 定义的能力边界、权限规则或业务规则在代码中缺失 → `P0`
- PRD 与代码在关键校验、权限、租户隔离或业务流程上冲突 → `P0`
- 代码已扩展新能力但 PRD 未更新语义说明 → `P1`
- 如接口说明或路由存在问题，单独记录，不要求 PRD 补端点列表

## 失败处理
- 参数为空：提示使用示例。
- 模块不存在：提示可用模块来源是 `docs/prd/**/*.md`。
- agent 调用失败：记录失败模块并继续其他模块（`--all` 模式）。

## 质量门禁
- 只读检查，不修改业务代码。
- 所有差异项必须可定位到文件或 PRD 条目。

## 相关引用
- `agents/backend-consistency.md`
- `SKILL.md`
