# Shopify 验收规范

`shopify-accept` 只读验收的关注点与底线。公共结论、分级、报告和结构化返回按验收前必须读取的 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md`。证据要求遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`。

## 必查项

按当前 phase 与设计声明的交付面检查；未涉及的 proxy、admin 或扩展标记不适用及原因，不要求为验收新增这些交付物。

1. **app proxy 验签**：全部 proxy 路由先验签后处理；不存在绕过验签的路径；`logged_in_customer_id` 为空时有明确降级而不是误判顾客。
2. **scopes 最小化**：`shopify.app.toml` 的 scopes 与设计声明的权限一致，无未使用 scope；新增 scope 有设计依据。
3. **PII 处理**：顾客数据的存储与展示范围与设计一致；不在日志、错误消息或店面响应中泄露无关顾客数据。
4. **扩展落位**：theme app extension 的 block 在主题编辑器可见且挂载点渲染；customer account 扩展页面入口存在。扩展交付不依赖对主题文件的直接修改。
5. **admin 页可访问**：嵌入页在 Shopify 管理后台可打开，页面操作走 App Bridge/管理会话客户端，无浏览器端直连 Admin API。
6. **设计一致性**：实现与 `shopify.md` 分端设计的契约（proxy 路径、operation、字段）一致；文件影响范围内无设计未声明的交付物。

## 证据底线

- dev/test 的验证命令证据真实存在（type-check/build/定向测试输出、冒烟观察记录）；缺环境执行的项标记未验证，不得推断通过。
- 报告按公共验收协议，记录当前 shopify-app/shopify-extension phase、专项门禁证据及拒绝时的修复责任范围。
