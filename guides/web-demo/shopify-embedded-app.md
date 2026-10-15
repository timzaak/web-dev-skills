# Shopify admin 嵌入页 Demo 要点

Shopify admin 嵌入式应用页面的 web-demo（Playwright）在通用 Demo 规范之上的增量约束。适用于 Polaris web components（`s-*`）+ App Bridge 的 React Router 模板项目；页面行为与验证入口以目标项目设计与 `scripts/index.md` 为准。

## 页面定位与会话

- 目标地址是 admin 预览 URL（店铺侧稳定）：`https://admin.shopify.com/store/<store>/apps/<client_id>` + 应用内路径（如 `/app`）。
- 应用渲染在 **iframe 内**（dev 隧道域名，如 trycloudflare.com）：`page.frameLocator('iframe[src*="<隧道域名特征>"]')`。隧道每次启动变化，按域名特征匹配。
- 打开页面后等待 iframe `load` 完成再交互：admin 加载期可能**重挂载**应用 iframe，过早点击会落在被替换的旧实例上（点击成功但无任何效果）。关键导航点击（进入编辑页、向导下一步等）带「目标未出现则重点一次」兜底。
- 商家会话承载（自动化 Chrome + CDP 附加 / 凭据回退）、登录与网络代理见 [Shopify 本地环境与商家会话](${CLAUDE_PLUGIN_ROOT}/guides/shopify/environment.md)。

## Polaris web components（s-*）交互（2026-10 实测）

| 交互 | 正确做法 | 反例 |
| --- | --- | --- |
| `s-button` 点击 | 点 shadow DOM 内层原生按钮：`[data-testid=…] button`（宿主不生成布局盒，boundingBox=null） | 点击宿主元素——随机丢失且无报错 |
| `s-select` 选择 | 对内层原生 `<select>` 直接 `selectOption(value)` | 点击宿主展开（永不 actionable，30s 超时） |
| `s-text-field` / `s-number-field` 输入 | `[data-testid=…] input` 后代选择器穿透开放 shadow DOM | —— |
| 禁用态断言 | 宿主用 `toHaveAttribute('disabled')`（反射属性但不映射原生 ARIA）；原生控件（datetime-local 等）仍可 `toBeDisabled()` | 对 `s-*` 宿主用 `toBeDisabled()`——恒判为可用 |
| 标题断言 | `s-page` / `s-section` 的 heading 是**宿主属性**：属性选择器 `s-page[heading="…"]` | 文本匹配（hasText/getByText）匹配不到属性值 |
| 同页多个 `s-modal` | 确认/取消按钮 testid 按弹窗唯一化（如 `confirm-end-ok` / `confirm-delete-ok`），点击前等内层按钮可见 | 全页共用同一 testid + `.first()`——命中隐藏弹窗的按钮 |

## App Bridge ResourcePicker

- 弹层以 **admin 顶层 DOM 的 dialog** 渲染：既不是独立 iframe，也不在应用 iframe 内。用 `page.getByRole('dialog').filter({ hasText: … })` 在顶层页定位。
- 列表项是整行接管的 ResourceItem：点击 `div[aria-label^="Select: …"]` 行本身（复选框 input 与其 label 均被该行遮盖，hit-target 永不满足）。
- 确认按钮是弹层内**精确** `Select`（`getByRole('button', { name: /^select$/i })`）；不要在 admin 全局作用域按前缀匹配（会命中其他按钮）。
- 选择结果提交后以标题快照 chip 回显在应用 iframe 表单内，作为持久断言点。

## 数据与断言

- 业务数据经 admin UI 操作创建（真实用户路径），名称带可追踪前缀（如 `[E2E]`），项目清理入口登记 `scripts/index.md`；运行前后各清理一次，只清本前缀。
- 时间断言按店铺时区口径：运行时从页面标注读取 ianaTimezone，用 `Intl.DateTimeFormat({ timeZone })` 换算壁面时间，不硬编码时区。
- 关键断言落在持久业务状态（列表行、状态徽章、字段持久值、禁用态属性、chip），不依赖自动消失的 toast；应用固定文案可作断言依据（硬编码中文文案稳定）。
