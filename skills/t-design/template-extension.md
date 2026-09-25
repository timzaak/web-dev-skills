# [方案名称] Chrome 扩展技术设计

主文档：`.ai/design/[feature].md`。仅描述扩展交付；后端契约引用来源，不复制字段定义。

## 1. 目标与范围

- [本端交付目标、范围外项、项目 WXT 版本、最低 Chrome 支持范围与实际目录；使用有版本门槛的 API 时说明兼容策略]

## 2. 需求来源与决策追踪

| Decision ID | 状态 | 设计落点 | 说明 |
|---|---|---|---|
| `DEC-[feature]-001` | Applied / Not Applicable / Superseded | [章节] | [依据] |

- [需求/用户故事/纯技术预研引用及验收目标]

## 3. 现有实现分析

- [真实入口、manifest、消息、存储、可复用模块与受影响边界]

## 4. 入口与交互

| 入口/上下文 | 承载目标 | 交互与反馈 | 关闭/导航/重启后的行为 |
|---|---|---|---|
| [实际入口] | [目标] | [主路径及错误反馈；无 UI 时说明] | [生命周期] |

## 5. 权限与上下文

- permissions / host_permissions / matches / CSP：[增量、需求或 DEC 依据、按需采用的 activeTab/可选权限、申请时机与拒绝/撤销路径]
- 特权操作及请求归属：[调用方、执行方、允许的站点/操作、凭据访问边界]
- content script（适用时）：[注入方式、匹配范围与执行 world；宿主导航、扩展更新/上下文失效后的取消、清理和恢复]
- 注入 UI（适用时）：[隔离方式、portal、重复注入与挂载/卸载条件]
- worker（适用时）：[监听注册、状态恢复、定时/幂等、失败重试边界]

## 6. 消息与存储

### 6.1 API 依赖

- 契约源：[backend.md 或现有 OpenAPI/SDK；无后端时明确不适用并删除示例行]

| Operation ID | 方法 | 路径 | 使用的请求字段 | 使用的响应字段 | 用途 |
|---|---|---|---|---|---|
| [operationId] | [METHOD] | `/api/...` | [字段名] | [字段名] | [用途] |

### 6.2 扩展内部契约

- 消息：[集中定义位置、生产者/消费者、sender/payload 校验、响应/错误、超时/取消；采用 Port 时的断连与恢复]
- 存储：[key/区域、schema、数据真源、写入方与并发策略、迁移与失败恢复、watch 清理]
- UI 状态：[局部状态/按需 Zustand/Query 的归属，持久化与 hydration；不引入无需求依赖]

## 7. 测试与验收

- 局部 Vitest（按需）：[真实浏览器/场景验证难稳定覆盖的重要规则、可观察回归、覆盖缺口与定向脚本；无增量价值时写“不新增”及原因]
- 浏览器：[真实加载、消息/权限/生命周期的必要证据；fixture、宿主/stub 来源、环境模式和命令]
- 用户当前 Chrome：[按 `${CLAUDE_PLUGIN_ROOT}/guides/extension/live-browser.md` 规划 Chrome DevTools MCP 现场验证；目标页面/扩展、所需上下文与复现步骤，或不适用依据；证据要求遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/extension-acceptance-contract.md`]
- Demo：[需要扩展用户故事演示时声明 extension-demo 交付、`demo/e2e/extension/` 资产、fixture 环境模式和选择器影响；否则说明不适用]
- 构建：[实际 type-check/compile、build 和生产 manifest 路径]

## 8. 风险与验证动作

- [已确定方案的风险、验证动作及完成条件；用户裁决缺口返回主会话，不以假设推进]

## 9. 文件影响范围（扩展文件）

| 文件 | 操作 | 说明 |
|---|---|---|
| `[真实仓库路径]` | CREATE / MODIFY / DELETE | [变更与命名依据] |

同时列入本端依赖的 Demo 资产，由主文档汇总时标记 extension-demo。MODIFY/DELETE 路径必须存在，CREATE 父目录必须存在。
