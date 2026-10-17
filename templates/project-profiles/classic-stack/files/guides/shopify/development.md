# Shopify App 开发规范

`shopify-app` 与 `shopify-extension` 两个 phase 共用本规范。目标项目由 `/t-init --shopify` 基于 Shopify 官方 React Router 模板创建；真实目录、脚本名和模板版本以目标项目现状为准，本规范约束结构语义与跨项目稳定的行为。

## 工程结构语义

单工程全栈：React Router 7 framework mode 的一个应用同时承载服务端路由（loader/action）与 admin 嵌入页，没有独立的 backend/frontend 目录。

- **应用本体**（`shopify-app` phase）：React Router 路由与 loader/action、Prisma 数据模型与迁移、admin 嵌入页、app proxy 路由、internal API、业务逻辑。
- **扩展目录** `extensions/`（`shopify-extension` phase）：theme app extension 与 customer account UI extension，各自独立子目录与 `shopify.extension.toml`。
- **应用配置** `shopify.app.toml`：应用名、scopes 与 app proxy 的配置源；扩展自身配置在各自的 `shopify.extension.toml`，不在代码里重复声明。
- **Demo 资产** `demo/`：Playwright 店面 E2E，归 web-demo phase，不属于本阶段交付。

## admin 嵌入页

- 页面渲染在 Shopify 管理后台 iframe 内：布局与交互组件用 Polaris，宿主通信与导航用 App Bridge（模板已接线，优先复用模板封装而非自行初始化）。
- 服务端数据访问用模板提供的管理会话客户端（authenticated Admin GraphQL/REST client）；不在浏览器端直连 Admin API、不硬编码店铺域名。
- 页面路由遵循模板约定（如 `app._index`、嵌套路由）；新增页面域保持一个页面域一个责任闭环。

## app proxy（店面到 App 的可信通道）

- 在 `shopify.app.toml` 的 `[app_proxy]` 声明子路径（如 `campaign`）；店面请求 `<店铺域名>/apps/<子路径>/...` 由 Shopify 转发到应用路由。
- **验签是硬门禁**：每个 proxy 请求先按官方 HMAC 规则校验 `signature`（模板/官方库提供验证函数，复用而不重写算法），验签失败返回 401，不做任何业务处理。
- 验签通过后才能信任 `shop` 与 `logged_in_customer_id` 参数：`logged_in_customer_id` 存在时以此识别登录顾客；为空时按设计声明的访客权限处理，不得将用户输入的 email 视为已验证身份。
- 响应按请求用途选择 Liquid 模板页或 JSON；面向店面页面的 HTML 响应遵守 app proxy 的内容类型要求。

## theme app extension（店面挂载）

- 交付物是 app block：Liquid 渲染挂载点容器 + 独立打包的前端资产（原生 TS/JS 或项目选定方案，不依赖 React Router 宿主）。
- 商家在主题编辑器把 block 拖到模板位置；block 资产通过 block settings 接收配置，数据请求走 app proxy 路径（同域、可识别顾客）。
- 扩展资产构建由扩展目录自身的构建流程负责（`shopify app dev/build` 触发）；不在应用本体路由里内联店面脚本。

## customer account UI extension（顾客个人中心页）

- 用 customer account 扩展的整页（full-page）目标在顾客账户中心增加设计声明的自定义页面；目标与入口在 `shopify.extension.toml` 声明。
- 扩展运行在 Shopify 托管的沙盒环境：不能用相对路径请求 app proxy，接口调用按扩展 API 的约束走；顾客身份来自扩展提供的会话上下文，不自行解析 cookie。
- 业务数据归属、跨店铺隔离键、顾客身份与访客权限以目标项目 PRD / Decision Log 为准；设计明确各交付面如何验证身份与授权，不从示例推导 email 匹配规则。缺少会改变业务含义的决定时交回编排层裁决。

## 数据与迁移

- 数据模型用 Prisma：schema 变更走 `prisma migrate dev` 生成迁移；部署侧按模板的数据库方案执行迁移（模板默认 SQLite + docker 迁移），不在业务代码里做运行时建表。
- 业务数据存储位置由设计声明；应用数据库与 Shopify 侧（customer tag、metafield、metaobject）的读写边界必须可追溯到需求，不因模板存在 Prisma 就决定业务数据归属。

## CLI 工作流与部署时机

- 开发：`shopify app dev` 连接真实店铺的 dev 版本（Cloudflare 隧道），admin 页、扩展、proxy 均可即时预览；扩展与配置变更由 CLI 推送。
- 新增扩展：`shopify app generate extension` 生成骨架后放入 `extensions/`。
- **部署时机**：`/t-push` 只负责 git 提交推送；`shopify app deploy`（及数据库迁移）是 push 之后由用户显式执行的独立动作，不并入任何 skill 自动触发。
- 分发方式为 custom distribution（面向自家店铺）时无 App Store 审核与计费集成；不要为上架流程预留代码路径。

## scopes 与权限

- scopes 在 `shopify.app.toml` 声明并保持最小集合；新增 scope 需要重新授权，视为影响店铺的变更，在设计文档记录理由。
