# Shopify 测试、验证、验收与 Demo 规范

适用于 `shopify-app` / `shopify-extension` 阶段的 Vitest 测试、完成前验证、`shopify-accept` 只读验收，以及 Shopify admin 嵌入页的 Playwright Demo。工程结构与本地环境见 [Shopify 开发规范](${CLAUDE_PLUGIN_ROOT}/guides/shopify/development.md)。

## 1. Vitest 测试边界（test slot）

测试分层原则：真实用户路径（店面、顾客账户页、admin 操作流）进 web-demo 的 Playwright，accept 只读复核证据；仅当 Demo 难以稳定覆盖某条重要可观察回归时，才为可独立运行的纯逻辑写 Vitest。不为覆盖率数字生成用例。

值得写局部测试的内容：

- app proxy 验签函数：合法签名通过、篡改/过期签名拒绝、必填参数缺失拒绝。
- loader/action 中可独立提取的纯业务逻辑：设计声明的业务规则、状态转换、身份与数据访问边界。
- 扩展辅助模块：配置解析、数据变换。

不写的内容：

- admin 页面的 DOM/组件测试——Polaris 页面由 accept 与冒烟验证覆盖。
- Playwright 用例——店面与 admin 用户故事归 web-demo/dev，本阶段不碰浏览器测试。
- 对 Shopify API 客户端的 mock 全家桶——loader 中薄封装不测，测其调用的纯逻辑。
- 框架（Prisma、React Router、Vitest）已保证的行为，`renders X` 静态文本断言与 CSS class 断言。

执行：定向命令以项目实际脚本为准（如项目根 `npm run test -- [pattern]`）；官方模板默认不带 test 脚本，项目未提供时先补齐入口或记录受阻，不静默跳过。测试资产编写与定向执行遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的 Test Execution Consolidation。

## 2. 完成前验证与 `shopify app dev` 冒烟

### 必跑命令（dev task 收尾与 `/t-push` 门禁）

在项目根执行；类型检查与构建是门禁，缺入口时先补齐或记录受阻，不静默跳过：

- 类型检查：优先 `npm run typecheck`，其次 `npm run type-check`；沿用项目脚本中的 React Router typegen 等前置动作，不用裸 `tsc` 替代。
- 应用构建：`npm run build`（官方模板为 React Router build）。
- lint：有实际脚本时执行 `npm run lint`。
- 扩展构建：改动涉及扩展或其共享依赖/配置时，执行 `npm run shopify -- app build`（根 `shopify` 脚本调用本地 CLI）；主题扩展需包含 Theme Check，不能只用 React Router build 的成功证明扩展有效。项目额外资产构建步骤按实际配置执行。

`/t-push` 的 Shopify 区域检查运行上述类型检查、应用构建及可用 lint；只要项目有 `extensions/**/shopify.extension.toml`，还运行扩展构建，覆盖根依赖/配置对扩展的影响。命令实现维护在 `${CLAUDE_PLUGIN_ROOT}/scripts/push.py`。已有项目使用其他包管理器时，阶段验证可用等价命令，但 push 需要上述稳定 npm script 入口。

### `shopify app dev` 冒烟（人工/主会话浏览器观察）

仅针对本 phase 与设计涉及的交付面，无法离线验证的运行时行为按以下标准判定，需要登录店铺账号；执行环境不具备时记录为未验证并交回编排层，不得用构建通过冒充：

1. dev server 启动且输出隧道 URL，无致命报错。
2. admin 嵌入页：在 Shopify 管理后台打开应用页面，Polaris 页面渲染、无控制台致命错误。
3. app proxy：请求 `/apps/<子路径>/...`，合法签名返回业务响应，篡改签名返回 401。dev store 默认开启店面密码保护（全部店面路径 302 → `/password`）：先按 [Shopify 开发规范](${CLAUDE_PLUGIN_ROOT}/guides/shopify/development.md) 用 `STOREFRONT_PASSWORD` 解锁再请求 proxy 路径；返回**应用侧响应**即转发到达应用（无对应路由时应用自身 404 即为转发生效）。
4. theme app extension：主题编辑器出现 app block，拖入模板后挂载点渲染。
5. customer account 扩展：顾客账户中心出现自定义页面入口且页面可打开。

验证命令输出与冒烟观察结果按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md` 写入任务证据；`shopify app deploy` 不属于本阶段验证（部署在 `/t-push` 之后由用户显式执行）。

## 3. 只读验收规范（shopify-accept）

公共结论、分级、报告和结构化返回按验收前必须读取的 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md`；证据要求遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`。

按当前 phase 与设计声明的交付面必查（未涉及的 proxy、admin 或扩展标记不适用及原因，不要求为验收新增交付物）：

1. **app proxy 验签**：全部 proxy 路由先验签后处理；不存在绕过验签的路径；`logged_in_customer_id` 为空时有明确降级而不是误判顾客。
2. **scopes 最小化**：`shopify.app.toml` 的 scopes 与设计声明的权限一致，无未使用 scope；新增 scope 有设计依据。
3. **PII 处理**：顾客数据的存储与展示范围与设计一致；不在日志、错误消息或店面响应中泄露无关顾客数据。
4. **扩展落位**：theme app extension 的 block 在主题编辑器可见且挂载点渲染；customer account 扩展页面入口存在。扩展交付不依赖对主题文件的直接修改。
5. **admin 页可访问**：嵌入页在 Shopify 管理后台可打开，页面操作走 App Bridge/管理会话客户端，无浏览器端直连 Admin API。
6. **设计一致性**：实现与 `shopify.md` 分端设计的契约（proxy 路径、operation、字段）一致；文件影响范围内无设计未声明的交付物。

证据底线：dev/test 的验证命令证据真实存在（type-check/build/定向测试输出、冒烟观察记录）；缺环境执行的项标记未验证，不得推断通过。报告按公共验收协议记录当前 `shopify-app`/`shopify-extension` phase、专项门禁证据及拒绝时的修复责任范围。

## 4. Shopify admin 嵌入页 Demo 要点

适用于 Polaris web components（`s-*`）+ App Bridge 的 React Router 模板项目在通用 Web Demo 规范之上的增量约束；页面行为与验证入口以目标项目设计与 `scripts/index.md` 为准。

### 页面定位与会话

- 目标地址是 admin 预览 URL（店铺侧稳定）：`https://admin.shopify.com/store/<store>/apps/<client_id>` + 应用内路径（如 `/app`）。
- 应用渲染在 **iframe 内**（dev 隧道域名，如 trycloudflare.com）：`page.frameLocator('iframe[src*="<隧道域名特征>"]')`。隧道每次启动变化，按域名特征匹配。
- 打开页面后等待 iframe `load` 完成再交互：admin 加载期可能**重挂载**应用 iframe，过早点击会落在被替换的旧实例上（点击成功但无任何效果）。关键导航点击（进入编辑页、向导下一步等）带「目标未出现则重点一次」兜底。
- 商家会话承载（自动化 Chrome + CDP 附加 / 凭据回退）、登录与网络代理见 [Shopify 开发规范](${CLAUDE_PLUGIN_ROOT}/guides/shopify/development.md)。

### Polaris web components（s-*）交互（2026-10 实测）

| 交互 | 正确做法 | 反例 |
| --- | --- | --- |
| `s-button` 点击 | 点 shadow DOM 内层原生按钮：`[data-testid=…] button`（宿主不生成布局盒，boundingBox=null） | 点击宿主元素——随机丢失且无报错 |
| `s-select` 选择 | 对内层原生 `<select>` 直接 `selectOption(value)` | 点击宿主展开（永不 actionable，30s 超时） |
| `s-text-field` / `s-number-field` 输入 | `[data-testid=…] input` 后代选择器穿透开放 shadow DOM | —— |
| 禁用态断言 | 宿主用 `toHaveAttribute('disabled')`（反射属性但不映射原生 ARIA）；原生控件（datetime-local 等）仍可 `toBeDisabled()` | 对 `s-*` 宿主用 `toBeDisabled()`——恒判为可用 |
| 标题断言 | `s-page` / `s-section` 的 heading 是**宿主属性**：属性选择器 `s-page[heading="…"]` | 文本匹配（hasText/getByText）匹配不到属性值 |
| 同页多个 `s-modal` | 确认/取消按钮 testid 按弹窗唯一化（如 `confirm-end-ok` / `confirm-delete-ok`），点击前等内层按钮可见 | 全页共用同一 testid + `.first()`——命中隐藏弹窗的按钮 |

### App Bridge ResourcePicker

- 弹层以 **admin 顶层 DOM 的 dialog** 渲染：既不是独立 iframe，也不在应用 iframe 内。用 `page.getByRole('dialog').filter({ hasText: … })` 在顶层页定位。
- 列表项是整行接管的 ResourceItem：点击 `div[aria-label^="Select: …"]` 行本身（复选框 input 与其 label 均被该行遮盖，hit-target 永不满足）。
- 确认按钮是弹层内**精确** `Select`（`getByRole('button', { name: /^select$/i })`）；不要在 admin 全局作用域按前缀匹配（会命中其他按钮）。
- 选择结果提交后以标题快照 chip 回显在应用 iframe 表单内，作为持久断言点。

### 数据与断言

- 业务数据经 admin UI 操作创建（真实用户路径），名称带可追踪前缀（如 `[E2E]`），项目清理入口登记 `scripts/index.md`；运行前后各清理一次，只清本前缀。
- 时间断言按店铺时区口径：运行时从页面标注读取 ianaTimezone，用 `Intl.DateTimeFormat({ timeZone })` 换算壁面时间，不硬编码时区。
- 关键断言落在持久业务状态（列表行、状态徽章、字段持久值、禁用态属性、chip），不依赖自动消失的 toast；应用固定文案可作断言依据（硬编码中文文案稳定）。
