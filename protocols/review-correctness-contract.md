# Correctness Review Contract

t-review 的审查角度、候选结构、Pass-Through、去重/三态验证和报告结构的单一事实源。

本契约只找正确性缺陷，不做代码质量清理；清理属于 `t-simplify`（角度定义见 `${CLAUDE_PLUGIN_ROOT}/protocols/simplify-cleanup-contract.md`）。本契约默认只输出可复核的报告，不修复缺陷；`--fix` 模式在报告写入后按 Fix Mode 一节处置发现。

## Review Angles

三个核心角度互不重叠，每个 finder agent 只负责注入的一个角度。以下角度翻译自 Claude Code 内置 `/code-review`（源版本 v2.1.269，2026-10-31 核对 npm v2.1.316 安装包）。新版按模型和 effort 路由，部分流程已混入清理/Conventions，或改为 inline 且不验证；本插件保留正确性审查与清理分离、独立 verifier 逐项三态判定和 Markdown 报告，验证调度采用下述小批量与高风险单项策略，不声称完整复刻新版默认流程。范围收集前读取 `${CLAUDE_PLUGIN_ROOT}/protocols/review-scope-contract.md`。

### Angle A — 逐行 diff 扫描（line-by-line diff scan）

逐行读 diff 的每个 hunk，然后 Read 每个 hunk 所在的完整函数——被触及函数中未变更行上的 bug 也在范围内（本次变更重新暴露或未能修复它们）。对每一行问：什么输入、状态、时序或平台会让这一行出错？关注反转/错误的条件、差一错误、null/undefined 解引用、缺失 `await`、falsy-zero 判断、复制粘贴用错变量、catch 中吞掉的错误、未转义的 regex 元字符。

### Angle B — 删除行为审计（removed-behavior auditor）

对 diff 删除或替换的每一行，说出它原本维护的不变量或行为，然后在新代码中搜索该不变量在哪里被重新建立。找不到即为候选：被移除的守卫、被丢弃的错误路径、被收窄的校验、删掉了覆盖真实场景的测试。

### Angle C — 跨文件追踪（cross-file tracer）

对 diff 变更的每个函数，找到它的调用方（Grep 符号）并检查变更是否破坏任何调用点：新增前置条件、返回结构变化、新抛出的异常、时序/顺序依赖。同时检查被调用方：同一批变更中的并行修改是否让某处调用变得不安全。

### 扩展角度（可选注入）

高风险模式追加以下两个角度（同源自 `/code-review` 的高强度档位），模式选择见 Dispatch：

- **Angle D — 语言/框架陷阱（language-pitfall specialist）**：扫描 diff 语言/框架的经典陷阱——例如 JS falsy-zero、`==` 强制转换、闭包捕获循环变量；Python 可变默认参数、迟绑定闭包；Go nil-map 写入、range 变量捕获；SQL 注入；时区/DST 漂移；浮点相等。标记 diff 引入的每个实例。
- **Angle E — 包装器/代理正确性（wrapper/proxy correctness）**：当变更新增或修改包装另一类型的类型（cache、proxy、decorator、adapter）时：检查每个方法都路由到被包装实例而不是绕回 registry/session/global——例如持有 `delegate` 字段的缓存 provider 用 `session.get(...)` 而不是 `delegate.get(...)` 解析 ID，会导致重入缓存或递归。同时检查包装器转发了调用方实际使用的全部方法。

## Dispatch

- 启动前根据变更风险选择并记录模式。普通模式：A / B / C 各一个 finder 并行，单角度最多 6 条候选；安全敏感、并发、公共 API 或大范围变更选择高风险模式：A / B / C / D / E 各一个 finder 并行，单角度最多 8 条候选，首轮验证后执行一次 Gap Sweep。
- 这是插件自身的调度规则，不根据 Claude Code 内置命令记忆的 effort 或当前模型偷偷更换流程。每个角度独立产出，同一行不同缺陷机制不得互相压制；没有发现时返回空列表，不凑数。
- 去重后给每个候选分配本次审查内稳定唯一的 `candidate_id`，验证、报告与修复沿用；后续查漏只为新候选增加 ID。
- finder 失败时只重试失败角度；verifier 的分批、漏项与恢复按 Verify 执行。重试后仍无法完成则标明审查未完成，不得当作空结果、输出“未发现缺陷”或继续 `--fix`。工具不可用时由 skill 显式转入 inline 降级，重新完成受影响范围。

## Candidate Structure

finder 按以下结构返回候选，上限见 Dispatch，按严重度排序：

```text
angle: A|B|C|D|E|S
candidates:
  - file:
    line:
    summary:          # 单行结论
    failure_scenario: # 具体输入/状态 → 错误输出或崩溃
```

- `file`/`line` 指向本次变更或被触及函数中的实际缺陷位置；指向未变更行时必须说明本次变更如何重新暴露或未能修复该路径，不扩成全仓历史缺陷审计。删除行以可定位的新代码位置或明确标注的旧版本位置引用。
- `failure_scenario` 必须具体：什么输入/状态触发、导致什么错误输出或崩溃；写不出触发路径的不算候选。
- finder 只读，不修改代码、不判断真伪。
- 疑似质量问题（重复、浪费、复杂度）不展开分析，只在 `summary` 中注明“疑似清理项，转交 t-simplify”。

## Pass-Through

finder 不得自行过滤“半信半疑”的候选：凡 `failure_scenario` 可命名的候选一律原样传递给验证阶段——finder 静默丢掉半信半疑的候选会绕过验证步骤，是漏报的主因。真伪判断属于 verifier。

## Dedup

主流程聚合全部候选后：指向同一行且同一缺陷机制的候选合并为一条，保留 `failure_scenario` 最具体的一条，角度标记合并。

## Verify（1-vote, 3-state）

### 分批与隔离

- 主流程在去重、分配稳定 `candidate_id` 后组织验证批次；每个候选只进入一个首轮批次，无候选时不启动 verifier。
- 普通候选优先按共享文件或调用链分组，每批以 3～5 条为目标、最多 5 条；不足时允许 1～2 条，不为凑数混入无关候选。全部候选都必须分配，不以批次上限截断总集合。
- 涉及并发时序、认证/授权、安全边界、数据丢失，或需要较长跨文件追踪、大量专属上下文的候选单独成批，并记录原因。这按候选的失败机制判断；整次审查属于高风险模式，不意味着其中所有普通候选都要单独验证。
- 每批新建一个独立于 finder 和其他批次的 verifier，可并行调用；不复用 finder 会话，不传批次外候选、其他 verifier 的判定或主流程预设结论。批内共享源码上下文，但每条候选必须独立取证和判定，不以一条成立/不成立推导其他项，不展开新审查。

### 最小受审上下文

- 每批只注入候选列表、已解析的审查范围/版本、相关 diff hunks、必要源码与适用项目约束；共享片段在批内只提供一次，不默认复制完整 diff。
- 同时提供可由 Read/Grep 访问的同一受审版本上下文入口，便于按需补读完整函数、调用方和守卫，节选不得成为证据边界。verifier 无 Bash，不能只给 Git 命令；PR、历史或其他分支的工作区不匹配时，由主流程提供受审版本源码内容或可读快照，不能拿当前工作区代替。
- 批次上下文过大时减少每批候选数，必要时拆为单项任务；仍缺必要 diff、受审源码或约束时，返回该项 `unverified` 及缺口，由主流程补齐后重试，不凭节选缺失推断“没有守卫”。

### 逐项判定

完成必要检查的每条候选返回且只返回以下三态之一：

1. **CONFIRMED** —— 能说出触发它的输入/状态以及错误的输出或崩溃，并引用对应代码行。
2. **PLAUSIBLE** —— 机制真实存在，触发条件不确定（时序、环境、配置）；说明什么能确认它。
3. **REFUTED** —— 与事实不符（代码并非如此）或已在别处防护；必须引用证明它的代码行。

保留 CONFIRMED 与 PLAUSIBLE，丢弃 REFUTED。证据不足时判 PLAUSIBLE 并说明确认途径，不得为保守而 REFUTED。

高风险模式尤其不能因“依赖运行时状态”就排除现实可达的并发竞争、冷缓存/错误路径上的空值、边界值、重试或部分失败、丢失正则锚点：触发条件待证实时保留 PLAUSIBLE。只有代码事实不符、类型/常量/不变量证明不可能、存在有效守卫，或纯风格且无可观察后果时才能 REFUTED，并给出证据。

未取得必要上下文、预算耗尽尚未检查或检查中断的候选进入 `unverified`，不能伪装成 PLAUSIBLE 或 REFUTED。PLAUSIBLE 表示已检查并发现机制真实、仅触发条件待证实。

验证输出结构（单项批次也使用相同列表）：

```text
results:
  - candidate_id:
    file:
    line:
    verdict: CONFIRMED|PLAUSIBLE|REFUTED
    evidence:       # 可引用的代码行；PLAUSIBLE 还需确认途径
unverified:
  - candidate_id:
    reason:         # 缺失上下文、未完成的检查或预算耗尽
```

无对应项的列表返回 `[]`。每个输入 `candidate_id` 必须恰好出现在 `results` 或 `unverified` 之一，不能重复、合并判定或遗漏。主流程校验 ID 覆盖、三态及所需证据；保留可可靠关联的有效结果，仅补齐并重试未验证、漏项、重复或无效项，不把已完成项及其判定带入重试。未知 ID 不作为新发现；若输出无法可靠映射到输入，整批视为失败并重试。重试后仍失败，保留已有证据并报告未完成，不输出干净结论、不进入 `--fix`。重跑按共享范围契约重新收集当前范围；不把旧批次结论套到新版本。

输出完整审查结论或进入修复前，首轮与查漏的每个候选都必须获得一个有效三态结果；`unverified` 和失败调用不是“排除”，也不计入三态数量。未完成时仍按 Report 写入已有结果及验证缺口，结论标明审查未完成。inline 模式沿用结构及覆盖门禁，但明确证据来自主会话自检，不声称独立验证。

## Gap Sweep

仅高风险模式在首轮验证后执行一次：新建一个 `review-finder`，注入同一范围、已验证候选及判定，以 `angle: S` 只找尚未列出的缺陷，不重新论证已有结论。重点检查移动/抽取时丢失的守卫或锚点、只计算一次的默认值、非确定性 hash、锁范围缩小、有副作用的谓词、测试 setup/teardown 不对称、配置默认值翻转。

最多返回 8 条新候选，无新增则返回空列表。新增项与已有项按 Dedup 去重后，按 Verify 同样分批或单项验证，不重验已有有效结果；验证完成后生成报告，不再次启动查漏。inline 模式在同一上下文追加一次查漏并自检新增项，报告注明降级。

## Fix Mode (`--fix`)

`--fix` 只改变报告之后的处置，不改变审查、验证与报告本身：

- 修复只发生在报告成功写入之后；finder/verifier 阶段与原始审查结论保持只读。应用前按共享范围契约核对本地版本；目标不匹配则 pending，不自动切分支或覆盖文件。
- CONFIRMED 发现由主会话切换到受影响端的 dev 角色边界修复：从 `${CLAUDE_PLUGIN_ROOT}/agents/` 读取对应的 dev agent 规范（`backend-dev.md`、`frontend-dev.md`、`extension-dev.md`、`miniapp-dev.md`、`flutter-dev.md`、`shopify-dev.md`、`web-demo-dev.md`、`extension-demo-dev.md`、`flutter-demo-dev.md`）作为当前角色边界（与 `t-super-run` 的主会话角色切换一致），不为此新派 subagent。
- PLAUSIBLE 发现先按其 `failure_scenario` 复现或确认；能确认的视同 CONFIRMED 修复，无法确认的保留为 pending 并写明确认途径。
- 会改变预期行为的修法跳过并标记 pending；不得用弱化断言、放宽校验、改需求含义或改写 verifier 结论的方式消除发现。
- 修复与下游门禁消费完整 CONFIRMED/PLAUSIBLE 集合，不受报告摘要的 8 条上限约束；每条修复后运行覆盖所改文件的最小定向验证，立即按 `candidate_id` 把结果写入同一报告的 `## Fixes`，不等整批完成才写回。报告写入失败则停止后续修复；恢复时先核对实际代码与已记结果，避免重复应用。修复使阶段证据失效时交回编排层补跑必要回归并重新独立 accept，不能把 fixed 当作重新验收通过。
- 同一发现连续三次修复失败且无新证据时标记 blocked 并停止，保留失败证据。

## Report

写入 `.ai/quality/review-[YYYYMMDD-HHMMSS].md`：

```text
# Correctness Review 报告 [YYYYMMDD-HHMMSS]

## 审查范围
- diff 来源: 默认范围 | 指定 target | 本会话已修改/用户指定文件
- 实际基准 / HEAD / 未提交变更（按共享范围契约记录）
- 文件数 / 变更行数
- 模式: 普通 / 高风险；实际执行的角度、验证数与查漏结果；完整 / 未完成 / inline

## 验证覆盖
- 各批次的 candidate_id；单项隔离原因；批次数 / 验证调用数（含重试）
- 未验证或失败项的完整候选、缺口原因、重试结果与恢复入口；inline 时标明自检

## 发现（按严重度降序，上限 8 条）
- candidate_id | file:line | 角度 | verdict | summary
  - failure_scenario
  - 证据: 引用的代码行或调用点

## 已排除
- candidate_id | file:line | 角度 | REFUTED 原因及证据

## 结论
- N 项 CONFIRMED / M 项 PLAUSIBLE；或未发现正确性缺陷
- 下一步: 修复入口（t-super-run / 主会话确认后修复），或确认可进入 t-simplify / t-push

## Fixes（仅 --fix）
- candidate_id | file:line | fixed | 修复说明 | 验证命令与结果
- candidate_id | file:line | pending | 原因或确认途径
```

“发现”摘要最多展示 8 条；超出时在同一报告追加 `## 完整发现集`，保留全部 CONFIRMED/PLAUSIBLE 的定位、failure_scenario、证据和处置状态。结论统计与 `## Fixes` 覆盖完整集合，未展示在摘要中不代表已排除或已解决；中断恢复从完整集合继续。无存留发现时“发现”节为空并如实写入结论。

恢复旧报告时，缺少 `candidate_id` 可按完整发现集顺序补充稳定 ID，不改写原结论；若完整集合或受审版本无法还原，保留旧报告并重新审查当前范围，不能直接按旧行号修复。

inline 降级模式（Agent tool 不可用）的报告必须在结论中声明：这是主会话 inline 审查，未经独立 verifier 验证；高风险模式还需说明是否执行查漏。审查未完成时报告缺失步骤与恢复入口，不给出可进入下游的干净结论。
