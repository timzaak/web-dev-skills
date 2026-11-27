# Shopify App 开发规范

`shopify-app` 与 `shopify-extension` 两个 phase 共用本规范。目标项目由 `/t-init`（Shopify 场景）基于 Shopify 官方 React Router 模板创建；真实目录、脚本名和模板版本以目标项目现状为准，本规范约束结构语义与跨项目稳定的行为。

测试、验证、验收与嵌入式页面 Demo 规范见 [Shopify 验证与验收规范](${CLAUDE_PLUGIN_ROOT}/guides/shopify/quality.md)。

## 工程结构语义

单工程全栈：React Router 7 framework mode 的一个应用同时承载服务端路由（loader/action）与 admin 嵌入页，没有独立的 backend/frontend 目录；店面 UI 是扩展交付的资产，不是应用路由页面。

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

## 数据、CLI 与 scopes

- 数据模型用 Prisma：schema 变更走 `prisma migrate dev` 生成迁移；部署侧按模板的数据库方案执行迁移（模板默认 SQLite + docker 迁移），不在业务代码里做运行时建表。
- 业务数据存储位置由设计声明；应用数据库与 Shopify 侧（customer tag、metafield、metaobject）的读写边界必须可追溯到需求，不因模板存在 Prisma 就决定业务数据归属。
- 开发：`shopify app dev` 连接真实店铺的 dev 版本（Cloudflare 隧道），admin 页、扩展、proxy 均可即时预览，扩展与配置变更由 CLI 推送；新增扩展用 `shopify app generate extension` 生成骨架放入 `extensions/`。
- **部署时机**：`/t-push` 只负责 git 提交推送；`shopify app deploy`（及数据库迁移）是 push 之后由用户显式执行的独立动作，不并入任何 skill 自动触发。
- 分发方式为 custom distribution（面向自家店铺）时无 App Store 审核与计费集成；不要为上架流程预留代码路径。
- scopes 在 `shopify.app.toml` 声明并保持最小集合；新增 scope 需要重新授权，视为影响店铺的变更，在设计文档记录理由。

## 本地环境、CLI 与商家会话

项目实际值（org / app / dev store / 端口 / 凭据文件）以目标项目 `scripts/index.md` 登记为准，本节只约束行为模式与排障路径。

### CLI 登录与关联事实

- 登录探测：短超时（60–90s）运行 `shopify app dev`，输出包含 Preview URL / Dev store / Access scopes 即已登录且已关联；也可检查 CLI 配置缓存中本目录的 appId/orgId。未登录时由用户在终端交互登录（任意需登录的 CLI 命令会触发），不伪造登录态或 client_id。
- 需要登记的关联事实：org、app 名称与 client_id、dev store 域名、admin 预览 URL 形态 `https://admin.shopify.com/store/<store>/apps/<client_id>`（店铺侧地址稳定，作为 Demo BASE_URL）。
- CLI 非交互环境（CI/管道）下需要登录的命令会以 `Failed to prompt` 失败：这不是配置错误，回到交互终端完成登录即可。

### dev server 与常见故障

- `shopify app dev` 运行期间 Cloudflare 隧道域名每次启动变化（trycloudflare.com）；依赖隧道的定位用域名特征匹配，不硬编码具体值。
- **残留进程锁 Prisma DLL**：停止 dev server 后 node 子进程可能残留并锁定 `node_modules/.prisma/client/query_engine-*.dll.node`，下次启动 `npx prisma generate`（pre-dev 命令）报 `EPERM rename` 失败。处置：按进程已加载模块扫描定位（PowerShell `Get-Process node` → `Modules` 匹配本项目 query_engine 路径）得到 PID 后 taskkill，再重启；不要盲目结束全部 node 进程。
- 修改服务端模块（如 `*.server.ts`）后行为未变化时，先怀疑 vite dev 未热加载，重启 dev server 验证，不要反复改代码。

### 网络代理

- 需要代理访问 Shopify 的环境：探测本机代理端口（Clash Verge/mihomo 常见 `7890`；也可读主浏览器 ZeroOmega/SwitchyOmega 配置存储中 fallbackProxy 指向的 host:port），并以 `curl -x <proxy> https://www.cloudflare.com/cdn-cgi/trace` 验证出口可用（看 loc/colo 非本机直连出口）。
- 注意监听绑定形态：代理客户端常监听 `0.0.0.0:<port>`，只 grep `127.0.0.1:<port>` 会漏判。
- 自动化 Chrome 经 `--proxy-server` 指向同一端口，与用户主浏览器走同一条链路；配合 `--proxy-bypass-list="<-loopback>"` 放行本机回环。

### 商家会话承载（web-demo 身份基础）

约束事实（2026-10 实测）：

- Chrome ≥136 禁止对默认用户数据目录开远程调试端口，无法附加用户日常主浏览器实例。
- Shopify 登录页有 Cloudflare 挑战 + 隐形验证码（登录按钮 `captcha__submit` 禁用等待放行）：全新浏览器上下文自动登录不可靠；无头 bundled chromium 会被 Cloudflare 直接拦截。
- 开启 2FA 的账号无法自动登录。

**主方案——专用自动化 Chrome 附加会话**：

1. 启动专用实例：`chrome.exe --user-data-dir=<项目外专用目录> --remote-debugging-port=<port> --proxy-server=<本机代理> --proxy-bypass-list="<-loopback>" --no-first-run --no-default-browser-check`（独立 user-data-dir 与正在运行的主浏览器实例可共存）。
2. 用户在该窗口**人工登录一次** admin，会话持久保存在该 user-data-dir，后续运行免登录。
3. Playwright `chromium.connectOverCDP(url)` 附加，取默认上下文 `contexts()[0]` 共享会话；每个用例开新标签页、结束只关标签页（`connectOverCDP` 的 `browser.close()` 仅断开连接，不会关闭用户窗口）。
4. fixture 启动时探测会话有效性（导航 admin 预览 URL，落在登录页即明确报错提示重新人工登录），不静默重试。

**回退——凭据自动登录**：经 `.env.demo` 注入 `SHOPIFY_STORE_EMAIL` / `SHOPIFY_STORE_PASSWORD`（须未开 2FA），UI 登录 + storageState 运行内复用；2FA 与 Cloudflare 拦截时明确失败，不保证可用。

**凭据文件** `.env.demo`（`.gitignore` 的 `.env.*` 规则覆盖，不入库）：`SHOPIFY_STORE_EMAIL`、`SHOPIFY_STORE_PASSWORD`、`STOREFRONT_PASSWORD`、`CHROME_CDP_URL`。

### 店面密码与 app proxy 店铺侧验证

- dev store 默认开启店面密码保护：**全部**店面路径（含 `/apps/<子路径>/`）302 → `/password`，无法直接判定 proxy 转发是否到达应用。
- 验证转发：GET `/password` 取 authenticity_token → POST `password=<店面密码>` 解锁（落 cookie）→ 请求 `/apps/<子路径>/`；返回**应用侧响应**（如应用自身 404 页）即转发到达应用。店面密码经 `.env.demo` 的 `STOREFRONT_PASSWORD` 注入，验证不改动任何店铺设置。
