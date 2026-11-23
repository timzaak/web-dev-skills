# Extension Acceptance Contract

供 `extension-dev`、`extension-test`、`extension-accept`、`extension-demo-dev`、`extension-demo-accept` 及任务编排消费。领域检查对象见 [Extension 验证与验收规范](${CLAUDE_PLUGIN_ROOT}/guides/extension/quality.md)。

验收前必须读取 [公共验收协议](${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md)，公共输入、报告路径、问题分级、结论、结构化返回和只读边界均以其为准；公共证据复用、报告保留及状态消费不在此重复定义。本协议补充两项 Chrome 扩展专项规则：用户浏览器现场证据与扩展故事 Demo 门禁。

## 1. 用户浏览器现场证据（`extension` / `extension-demo` 共用）

- 报告额外记录 manifest/权限差异与必要现场上下文。
- 用户要求读取当前浏览器，或设计/任务验证依赖当前登录态、标签页状态、宿主网站与已安装扩展交互时，必须取得本次现场证据；纯逻辑单测、构建或独立 fixture 足以覆盖的任务可注明不适用，不强制连接个人 Chrome。
- 输入补充目标页面/场景、需核对的扩展和允许的操作范围；选择有歧义或影响验收目标的输入缺失时，返回主会话让用户裁决。接入和操作方法按 [用户 Chrome 调试](${CLAUDE_PLUGIN_ROOT}/guides/extension/live-browser.md)。
- 执行现场任务前核对实际角色可调用的浏览器工具；主会话已连接 MCP 不代表 subagent 自动可用。角色声明使用 `chrome-devtools` 服务名，其他客户端按实际命名映射。缺少工具时返回缺口，由主会话采集并传入证据，或配置后恢复；不得用 Bash 绕过工具限制。
- 证据至少记录采集时间、Chrome/MCP 版本（无法取得时明确未知）、目标 profile 的可区分标识与页面 URL/page ID、扩展 ID/版本及加载产物依据、复现步骤、预期/实际结果、实际覆盖的上下文、截图/日志来源及未验证项。使用现有任务输出或验收报告位置保存，截图等附件放报告同目录并引用；不新增状态文件或把凭据写入报告。
- accept 可执行只读观察或消费开发角色/主会话提供的上述证据，报告须标注采集者和来源；需要重载扩展或业务操作的复核交回开发角色/主会话。现场验证不能替代约定的独立回归，回归通过也不能抵消缺失的必要现场证据。
- 连接失败或现场已变化时保留证据并标记未验证；必要现场验证未完成按公共协议阻断。恢复后由开发角色/主会话重新确认现场和修复产物并采集新证据，再交 accept 复核；不得改连临时 profile 后宣称现场通过。

## 2. 扩展用户故事 Demo 验收（`extension-demo-accept`）

### 输入与范围

- 输入为目标 `demo/e2e/extension/**/*.e2e.ts` 文件或 `all`、设计与用户故事来源、构建命令和产物、环境模式、执行日志。只验收当前扩展演示范围，不扫描普通 Web Demo。
- `demo/e2e/extension/verification/` 保留给初始化基础设施验证，不属于用户故事演示。故事验收的 `all` 扫描排除此目录，显式传入时提示使用初始化验证入口；不将其判为故事 ACCEPTED 或为其编造故事映射。排除后没有故事用例时报告“无可验收用户故事”，不报告验收通过。批次发现复用 runner 已有的 verification 目录排除规则，初始化流程直接定向执行其中的 smoke。
- 报告额外记录故事/场景映射、实际加载产物/manifest、fixture 环境模式及隔离/清理证据。故事追溯按 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md` 的 Story Traceability。

### 专项门禁

- **MANDATORY**：用户故事来源存在且角色、动作、关键断言与验收目标一致；构建成功并确认 fixture 加载本次产物；整文件浏览器执行通过；profile、宿主/stub、数据清理可复核；必要现场证据完整。
- 不使用 skip、弱化断言或只检查 toast/测试 mock 来获得通过。权限、消息、存储与生命周期只要求覆盖设计和本次变更实际涉及的路径，不凭空增加全量要求。

## 3. 恢复与交接

必要现场证据或故事门禁失败/缺失按公共验收协议拒绝；环境/工具缺口先由主会话解除，再交 accept 复核，不空转重派。修复由 `extension-dev` / `extension-test` / `extension-demo-dev` 按归因负责，重建当前产物、确认加载产物并重跑受影响用例及必要整文件终验后重新验收；状态迁移沿用调用入口的 task/super-run 协议。
