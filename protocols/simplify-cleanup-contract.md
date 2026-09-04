# Simplify Cleanup Contract

t-simplify 的审查角度、finding 结构、去重/跳过/修复边界和报告结构的单一事实源。

本契约只做代码质量清理，不找正确性缺陷；正确性缺陷属于 `/code-review` 与各阶段 accept 的职责。

## Review Angles

四个角度互不重叠，每个 reviewer agent 只负责注入的一个角度。以下指引与 Claude Code v2.1.232 内置 `/simplify` 原文逐字对齐（提取来源见 SKILL.md），不得自行放宽或收窄：

### Reuse（复用）

标记新代码重新实现了代码库中**已有的东西**：用 Grep 检查共享/工具模块以及与变更相邻的文件，并点名应当改用的既有 helper。

### Simplification（简化）

标记 diff 新增的不必要复杂度：冗余或可推导的状态、只做微调的复制粘贴、深层嵌套、遗留的死代码。给出完成同样工作的更简形式。

### Efficiency（效率）

标记 diff 引入的浪费：冗余计算或重复 I/O、独立操作被串行执行、启动或热路径上新增的阻塞工作。同时标记由闭包或捕获环境构建的长生命周期对象——它们会让整个外围作用域在对象生命周期内无法释放（该作用域持有大值时即为内存泄漏）；应改为只拷贝所需字段的 class/struct。给出更省的替代做法。

### Altitude（抽象层级）

检查每处修改是否实现在正确深度，而不是脆弱的创可贴。在共享基础设施上叠加特例说明修得不够深——优先泛化底层机制，而不是继续加特例。

## Finding Structure

每个 reviewer 按以下结构返回 findings：

```text
findings:
  - file:
    line:
    summary:          # 单行结论
    cost:             # 具体代价：什么被重复、浪费或更难维护
    fix_hint:         # 建议修法（可选）
```

- `file`/`line` 指向本次 diff 范围内的位置；找不到精确行号时给最近的可定位位置。
- `cost` 必须具体可评估；写不出具体代价的发现不返回。
- reviewer 只读，不修改代码。

## Dedup

主流程聚合全部 findings 后：

- 指向同一行或同一机制的发现合并为一条，保留描述最具体的一条，角度标记合并。
- 仅描述风格差异、不构成独立代价的发现合并。

## Skip Rules

修复前逐条判断，以下三类跳过并在报告中记录原因，不与发现争论：

1. 修复会改变预期行为（对外语义、输出、错误路径）。
2. 修复需要明显超出本次审查 diff 的改动。允许的例外：为消除重复新建共享 helper 文件，并让 diff 内代码改用它；但不得修改 diff 外已有文件的既有逻辑。
3. 判定为误报。

## Report

写入 `.ai/quality/simplify-[YYYYMMDD-HHMMSS].md`：

```text
# Simplify 报告 [YYYYMMDD-HHMMSS]

## 审查范围
- diff 来源: @{upstream}...HEAD（或回退基准）+ git diff HEAD | 指定 target | 最近修改文件
- 文件数 / 变更行数

## 修复的发现
- file:line | 角度 | summary | 修复说明

## 跳过的发现
- file:line | 角度 | summary | 跳过原因（行为变化 | 超出范围 | 误报）

## 结论
- 已修复 N 项，跳过 M 项；或代码已干净
```

inline 降级模式（Agent tool 不可用）的报告必须在结论中声明：这是单主会话单遍审查，不是 4-agent 并行审查，读者不应对审查强度产生误判。

