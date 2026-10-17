# Shopify 本地环境与商家会话

CLI 登录、dev server、网络代理与商家会话承载的跨项目稳定做法。项目实际值（org / app / dev store / 端口 / 凭据文件）以目标项目 `scripts/index.md` 登记为准，本规范只约束行为模式与排障路径。

## CLI 登录与关联事实

- 登录探测：短超时（60–90s）运行 `shopify app dev`，输出包含 Preview URL / Dev store / Access scopes 即已登录且已关联；也可检查 CLI 配置缓存中本目录的 appId/orgId。未登录时由用户在终端交互登录（任意需登录的 CLI 命令会触发），不伪造登录态或 client_id。
- 需要登记的关联事实：org、app 名称与 client_id、dev store 域名、admin 预览 URL 形态 `https://admin.shopify.com/store/<store>/apps/<client_id>`（店铺侧地址稳定，作为 Demo BASE_URL）。
- CLI 非交互环境（CI/管道）下需要登录的命令会以 `Failed to prompt` 失败：这不是配置错误，回到交互终端完成登录即可。

## dev server 与常见故障

- `shopify app dev` 运行期间 Cloudflare 隧道域名每次启动变化（trycloudflare.com）；依赖隧道的定位用域名特征匹配，不硬编码具体值。
- **残留进程锁 Prisma DLL**：停止 dev server 后 node 子进程可能残留并锁定 `node_modules/.prisma/client/query_engine-*.dll.node`，下次启动 `npx prisma generate`（pre-dev 命令）报 `EPERM rename` 失败。处置：按进程已加载模块扫描定位（PowerShell `Get-Process node` → `Modules` 匹配本项目 query_engine 路径）得到 PID 后 taskkill，再重启；不要盲目结束全部 node 进程。
- 修改服务端模块（如 `*.server.ts`）后行为未变化时，先怀疑 vite dev 未热加载，重启 dev server 验证，不要反复改代码。

## 网络代理

- 需要代理访问 Shopify 的环境：探测本机代理端口（Clash Verge/mihomo 常见 `7890`；也可读主浏览器 ZeroOmega/SwitchyOmega 配置存储中 fallbackProxy 指向的 host:port），并以 `curl -x <proxy> https://www.cloudflare.com/cdn-cgi/trace` 验证出口可用（看 loc/colo 非本机直连出口）。
- 注意监听绑定形态：代理客户端常监听 `0.0.0.0:<port>`，只 grep `127.0.0.1:<port>` 会漏判。
- 自动化 Chrome 经 `--proxy-server` 指向同一端口，与用户主浏览器走同一条链路；配合 `--proxy-bypass-list="<-loopback>"` 放行本机回环。

## 商家会话承载（web-demo 身份基础）

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

## 店面密码与 app proxy 店铺侧验证

- dev store 默认开启店面密码保护：**全部**店面路径（含 `/apps/<子路径>/`）302 → `/password`，无法直接判定 proxy 转发是否到达应用。
- 验证转发：GET `/password` 取 authenticity_token → POST `password=<店面密码>` 解锁（落 cookie）→ 请求 `/apps/<子路径>/`；返回**应用侧响应**（如应用自身 404 页）即转发到达应用。店面密码经 `.env.demo` 的 `STOREFRONT_PASSWORD` 注入，验证不改动任何店铺设置。
