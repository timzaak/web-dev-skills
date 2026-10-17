# Extension Acceptance Contract

供 extension-dev、extension-test、extension-accept 及任务编排消费。领域证据见 [quality guide](${CLAUDE_PLUGIN_ROOT}/guides/extension/quality.md)。

## 输入与报告

输入：feature、变更范围、设计或适用的豁免依据、上游验证证据。
报告写入 `.ai/quality/extension-accept-[feature]-[YYYYMMDD-HHMMSS].md`，至少包含结论、门禁结果、manifest/权限差异、带文件或命令来源的问题、必要后续动作。

结构化返回遵循 [agent output](${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md)，补充 `acceptance_result` 和 `report_path`。`change_scope` 表示实际改动，不能把只读检查对象当作改动。

验收前按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md` 核查业务验证责任与证据复用；每次独立输出本轮验收结论，必要现场证据仍须符合本协议。

## 判定

### 用户浏览器现场证据

- 用户要求读取当前浏览器，或设计/任务验证依赖当前登录态、标签页状态、宿主网站与已安装扩展交互时，必须取得本次现场证据；纯逻辑单测、构建或独立 fixture 足以覆盖的任务可注明不适用，不强制连接个人 Chrome。
- 输入补充目标页面/场景、需核对的扩展和允许的操作范围；选择有歧义或影响验收目标的输入缺失时，返回主会话让用户裁决。接入和操作方法按 [用户 Chrome 调试](${CLAUDE_PLUGIN_ROOT}/guides/extension/live-browser.md)。
- 执行现场任务前核对实际角色可调用的浏览器工具；主会话已连接 MCP 不代表 subagent 自动可用。角色声明使用 `chrome-devtools` 服务名，其他客户端按实际命名映射。缺少工具时返回缺口，由主会话采集并传入证据，或配置后恢复；不得用 Bash 绕过工具限制。
- 证据至少记录采集时间、Chrome/MCP 版本（无法取得时明确未知）、目标 profile 的可区分标识与页面 URL/page ID、扩展 ID/版本及加载产物依据、复现步骤、预期/实际结果、实际覆盖的上下文、截图/日志来源及未验证项。使用现有任务输出或验收报告位置保存，截图等附件放报告同目录并引用；不新增状态文件或把凭据写入报告。
- accept 可执行只读观察或消费开发角色/主会话提供的上述证据，报告须标注采集者和来源；需要重载扩展或业务操作的复核交回开发角色/主会话。现场验证不能替代约定的独立回归，回归通过也不能抵消缺失的必要现场证据。
- 连接失败或现场已变化时保留证据并标记未验证；必要现场验证未完成按下方判定阻断。恢复后由开发角色/主会话重新确认现场和修复产物并采集新证据，再交 accept 复核；不得改连临时 profile 后宣称现场通过。

### 验收结论

- `REJECTED`：必要门禁失败/未完成，设计或验收目标未满足，或存在影响功能正确性、权限边界、凭据保护、CSP 的未解决缺陷；`task_completion.status=failed`。
- `ACCEPTED_WITH_IMPROVEMENTS`：必要门禁全部通过，仅有不影响验收目标和安全边界的维护性改进；`task_completion.status=success`。
- `ACCEPTED`：必要门禁通过且无未解决问题；`task_completion.status=success`。

问题可标 P0（无法继续/核心功能阻塞）、P1（功能或安全边界受损）、P2（维护性改进）；P0/P1 均阻断，不用“带改进通过”豁免。无法执行的必要检查标记未验证，不能计为通过；不适用项写明原因。

## 恢复与重复执行

验收只读检查源码；允许生成构建输出和报告。失败交回编排层，由 extension-dev 或 extension-test 修复后重跑相关检查及验收。每次验收写新报告并引用本次证据；旧报告保留，不把旧成功覆盖到本次未验证项。任务状态迁移沿用 [task state](${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md)。
