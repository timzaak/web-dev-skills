# [方案名称] Shopify 分端技术设计

主文档：`.ai/design/[feature].md`。本端覆盖 `shopify-app`（应用本体）与 `shopify-extension`（`extensions/` 交付面）两个 phase；backend 端适用时契约引用 `backend.md`，不复制字段定义。

## 1. 目标与范围

- [本端交付目标、范围外项、模板版本与项目实际目录]
- 交付面清单：

| 交付面 | 归属 phase | 本次是否变更 | 说明 |
|---|---|---|---|
| 应用本体（loader/action、Prisma、internal API） | shopify-app | 是/否 | [范围] |
| admin 嵌入页 | shopify-app | 是/否 | [页面域] |
| app proxy 路由 | shopify-app | 是/否 | [子路径与用途] |
| theme app extension | shopify-extension | 是/否 | [block 与挂载位置] |
| customer account UI extension | shopify-extension | 是/否 | [页面目标] |

## 2. 需求来源与决策追踪

| Decision ID | 状态 | 设计落点 | 说明 |
|---|---|---|---|
| `DEC-[feature]-001` | Applied / Not Applicable / Superseded | [章节] | [依据] |

- [需求/用户故事/技术预研引用及验收目标]

## 3. 现有实现分析

- [真实路由与 loader/action、`shopify.app.toml`（scopes、app proxy）、`extensions/` 清单与各自配置、Prisma schema 与迁移、可复用模块与受影响边界]

## 4. 数据模型

- [Prisma 模型、字段语义、关系与迁移；按"尽量简洁、当前必需"设计]
- Shopify 侧回写（customer tag / metafield / metaobject，适用时）：[数据、触发时机与理由；默认不适用]

## 5. 契约设计（app proxy / internal API）

契约源声明：[backend.md 适用时声明引用，删除下方清单职责；backend 不适用时本节是唯一契约源]

是否允许无契约及主文档同步要求，按 `${CLAUDE_PLUGIN_ROOT}/protocols/design-agent-output-contract.md` 的 Shopify 契约规则；适用时填写下表，不适用时删除空表并声明原因。

| Operation ID | 方法 | 路径 | 请求字段 | 响应字段 | 错误行为 | 调用方 |
|---|---|---|---|---|---|---|
| [operationId] | GET/POST | `/apps/<子路径>/...` 或 internal | [字段] | [字段] | [401/400/...] | [店面 block/客户账户页/admin] |

- 顾客识别语义：[`logged_in_customer_id` 的使用与为空时的降级路径；需求声明的数据归属、身份验证与访客权限规则]
- 验签：[复用模板/官方验证函数的声明；不重写算法]

## 6. admin 嵌入页

- [页面域清单与每页核心操作流（Polaris + App Bridge 体验描述：入口、操作路径、反馈、错误状态）；不规定组件 props]

## 7. 扩展交付（extensions/）

- theme app extension：[block 清单、Liquid 挂载点、block settings、前端资产构建方式；不通过主题文件直接修改交付]
- customer account UI extension：[整页目标、入口菜单、数据来源与需求声明的归属规则与扩展 API 约束下的接口调用方式]
- scopes：[当前集合、本次增量与理由；无变化时声明]

## 8. 测试与验收

- 局部 Vitest（按需）：[验签边界、设计声明的纯业务规则和数据访问边界的覆盖点；无增量价值时写"不新增"及原因]
- Demo：[店面、admin 或顾客账户用户故事演示时声明 web-demo 交付、`demo/e2e/` 资产与目标 URL（dev tunnel / dev theme 预览 / proxy 页面）选择器影响；否则说明不适用]
- `shopify app dev` 冒烟：[admin 页、proxy、扩展落位的判定点]
- 构建：[按 Shopify validation guide 列出实际类型检查、应用构建、适用的扩展构建 / lint 命令]

## 9. 风险与验证动作

- [已确定方案的风险、验证动作及完成条件；用户裁决缺口返回主会话，不以假设推进]

## 10. 文件影响范围（Shopify 文件）

| 文件 | 操作 | 归属 phase | 说明 |
|---|---|---|---|
| `[真实仓库路径]` | CREATE / MODIFY / DELETE | shopify-app / shopify-extension | [变更与命名依据] |

同时列入本端依赖的 Demo 资产，由主文档汇总时标记 web-demo。MODIFY/DELETE 路径必须存在，CREATE 父目录必须存在。
