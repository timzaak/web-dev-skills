# Correctness Review Contract

t-review 的审查角度、候选结构、Pass-Through、去重/三态验证和报告结构的单一事实源。

本契约只找正确性缺陷，不做代码质量清理；清理属于 `t-simplify`（角度定义见 `${CLAUDE_PLUGIN_ROOT}/protocols/simplify-cleanup-contract.md`）。本契约只输出可复核的报告，不修复缺陷。

## Review Angles

三个核心角度互不重叠，每个 finder agent 只负责注入的一个角度。以下指引与 Claude Code 内置 `/code-review` 原文逐字对齐（对齐版本 v2.1.269），不得自行放宽或收窄：

### Angle A — 逐行 diff 扫描（line-by-line diff scan）

逐行读 diff 的每个 hunk，然后 Read 每个 hunk 所在的完整函数——被触及函数中未变更行上的 bug 也在范围内（本次变更重新暴露或未能修复它们）。对每一行问：什么输入、状态、时序或平台会让这一行出错？关注反转/错误的条件、差一错误、null/undefined 解引用、缺失 `await`、falsy-zero 判断、复制粘贴用错变量、catch 中吞掉的错误、未转义的 regex 元字符。

### Angle B — 删除行为审计（removed-behavior auditor）

对 diff 删除或替换的每一行，说出它原本维护的不变量或行为，然后在新代码中搜索该不变量在哪里被重新建立。找不到即为候选：被移除的守卫、被丢弃的错误路径、被收窄的校验、删掉了覆盖真实场景的测试。

### Angle C — 跨文件追踪（cross-file tracer）

对 diff 变更的每个函数，找到它的调用方（Grep 符号）并检查变更是否破坏任何调用点：新增前置条件、返回结构变化、新抛出的异常、时序/顺序依赖。同时检查被调用方：同一批变更中的并行修改是否让某处调用变得不安全。

### 扩展角度（可选注入）

高风险或大范围变更（安全敏感、并发、公共 API 变更）时，调度方可追加注入以下两个角度（同源自 `/code-review` 的高强度档位），是否追加在启动 finder 前决定：

- **Angle D — 语言/框架陷阱（language-pitfall specialist）**：扫描 diff 语言/框架的经典陷阱——例如 JS falsy-zero、`==` 强制转换、闭包捕获循环变量；Python 可变默认参数、迟绑定闭包；Go nil-map 写入、range 变量捕获；SQL 注入；时区/DST 漂移；浮点相等。标记 diff 引入的每个实例。
- **Angle E — 包装器/代理正确性（wrapper/proxy correctness）**：当变更新增或修改包装另一类型的类型（cache、proxy、decorator、adapter）时：检查每个方法都路由到被包装实例而不是绕回 registry/session/global——例如持有 `delegate` 字段的缓存 provider 用 `session.get(...)` 而不是 `delegate.get(...)` 解析 ID，会导致重入缓存或递归。同时检查包装器转发了调用方实际使用的全部方法。

## Candidate Structure

finder 按以下结构返回候选，单角度最多 6 条、按严重度排序：

```text
angle: A|B|C|D|E
candidates:
  - file:
    line:
    summary:          # 单行结论
    failure_scenario: # 具体输入/状态 → 错误输出或崩溃
```

- `file`/`line` 指向本次 diff 范围内的位置；找不到精确行号时给最近的可定位位置。
- `failure_scenario` 必须具体：什么输入/状态触发、导致什么错误输出或崩溃；写不出触发路径的不算候选。
- finder 只读，不修改代码、不判断真伪。
- 疑似质量问题（重复、浪费、复杂度）不展开分析，只在 `summary` 中注明“疑似清理项，转交 t-simplify”。

## Pass-Through

finder 不得自行过滤“半信半疑”的候选：凡 `failure_scenario` 可命名的候选一律原样传递给验证阶段——finder 静默丢掉半信半疑的候选会绕过验证步骤，是漏报的主因。真伪判断属于 verifier。

## Dedup

主流程聚合全部候选后：指向同一行且同一缺陷机制的候选合并为一条，保留 `failure_scenario` 最具体的一条，角度标记合并。

## Verify（1-vote, 3-state）

对每条去重后的候选，由 verifier 逐条独立判定，返回且只返回以下三态之一：

1. **CONFIRMED** —— 能说出触发它的输入/状态以及错误的输出或崩溃，并引用对应代码行。
2. **PLAUSIBLE** —— 机制真实存在，触发条件不确定（时序、环境、配置）；说明什么能确认它。
3. **REFUTED** —— 与事实不符（代码并非如此）或已在别处防护；必须引用证明它的代码行。

保留 CONFIRMED 与 PLAUSIBLE，丢弃 REFUTED。证据不足时判 PLAUSIBLE 并说明确认途径，不得为保守而 REFUTED。

## Report

写入 `.ai/quality/review-[YYYYMMDD-HHMMSS].md`：

```text
# Correctness Review 报告 [YYYYMMDD-HHMMSS]

## 审查范围
- diff 来源: @{upstream}...HEAD（或回退基准）+ git diff HEAD | 指定 target | 最近修改文件
- 文件数 / 变更行数

## 发现（按严重度降序，上限 8 条）
- file:line | 角度 | verdict | summary
  - failure_scenario
  - 证据: 引用的代码行或调用点

## 已排除
- file:line | 角度 | REFUTED 原因（一句话）

## 结论
- N 项 CONFIRMED / M 项 PLAUSIBLE；或未发现正确性缺陷
- 下一步: 修复入口（t-run / 主会话确认后修复），或确认可进入 t-simplify / t-push
```

超出上限时按严重度截断；无存留发现时“发现”节为空并如实写入结论。

inline 降级模式（Agent tool 不可用）的报告必须在结论中声明：这是单主会话单遍审查，未经独立 verifier 验证。
