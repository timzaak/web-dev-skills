# Shopify 测试指南

测试分层原则：可独立运行的纯逻辑进 Vitest；真实用户路径（店面、顾客账户页、admin 操作流）进 web-demo 的 Playwright；accept 只读复核证据。不为覆盖率数字生成用例。

## Vitest 边界（shopify-app / shopify-extension 的 test slot）

值得写局部测试的内容：

- app proxy 验签函数：合法签名通过、篡改/过期签名拒绝、必填参数缺失拒绝。
- loader/action 中可独立提取的纯业务逻辑：设计声明的业务规则、状态转换、身份与数据访问边界。
- 扩展辅助模块：配置解析、数据变换。

不写的内容：

- admin 页面的 DOM/组件测试——Polaris 页面由 accept 与冒烟验证覆盖。
- Playwright 用例——店面与 admin 用户故事归 web-demo/dev，本阶段不碰浏览器测试。
- 对 Shopify API 客户端的 mock 全家桶——loader 中薄封装不测，测其调用的纯逻辑。

## 执行

- 定向命令以项目实际脚本为准，典型为项目根 `npm run test -- [pattern]`。
- 测试资产编写与定向执行遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的 Test Execution Consolidation。
