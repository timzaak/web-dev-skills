# Shopify 完成前验证

## 必跑命令（shopify-app 与 shopify-extension 的 dev task 收尾）

在项目根执行；类型检查与构建是门禁，缺入口时先补齐或记录受阻，不静默跳过：

- 类型检查：优先 `npm run typecheck`，其次 `npm run type-check`；沿用项目脚本中的 React Router typegen 等前置动作，不用裸 `tsc` 替代。
- 应用构建：`npm run build`（官方模板为 React Router build）。
- lint：有实际脚本时执行 `npm run lint`。
- 扩展构建：改动涉及扩展或其共享依赖/配置时，执行 `npm run shopify -- app build`（根 `shopify` 脚本调用本地 CLI）；主题扩展需包含 Theme Check，不能只用 React Router build 的成功证明扩展有效。项目额外资产构建步骤按实际配置执行。

`/t-push` 的 Shopify 区域检查运行上述类型检查、应用构建及可用 lint；只要项目有 `extensions/**/shopify.extension.toml`，还运行扩展构建，覆盖根依赖/配置对扩展的影响。命令实现维护在 `${CLAUDE_PLUGIN_ROOT}/scripts/push.py`。已有项目使用其他包管理器时，阶段验证可用等价命令，但 push 需要上述稳定 npm script 入口。

## `shopify app dev` 冒烟（人工/主会话浏览器观察）

仅针对本 phase 与设计涉及的交付面，无法离线验证的运行时行为按以下标准判定，需要登录店铺账号；执行环境不具备时记录为未验证并交回编排层，不得用构建通过冒充：

1. dev server 启动且输出隧道 URL，无致命报错。
2. admin 嵌入页：在 Shopify 管理后台打开应用页面，Polaris 页面渲染、无控制台致命错误。
3. app proxy：请求 `/apps/<子路径>/...`，合法签名返回业务响应，篡改签名返回 401。
4. theme app extension：主题编辑器出现 app block，拖入模板后挂载点渲染。
5. customer account 扩展：顾客账户中心出现自定义页面入口且页面可打开。

## 证据

验证命令的输出与冒烟观察结果按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md` 写入任务证据；`shopify app deploy` 不属于本阶段验证（部署在 `/t-push` 之后由用户显式执行）。
