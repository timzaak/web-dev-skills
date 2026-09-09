# Chrome 扩展开发规范

先读目标项目的 package.json、WXT 配置、入口和设计，确认目录、版本及 manifest 事实。默认代码目录为 `extension/`，已有项目沿用实际位置。

## 技术基线

- Chrome Manifest V3 + WXT + React + TypeScript。
- 存储使用 WXT 内置 storage（`wxt/utils/storage` 或项目已有自动导入），无需另装 `@wxt-dev/storage`；跨上下文请求用 `@webext-core/messaging` 集中定义协议，外部输入用 Zod 做运行时校验。
- Tailwind / Radix 按 UI 复杂度采用；简单 popup 优先组件局部状态，有跨组件状态需求再用 Zustand。
- 需要服务端缓存时在 UI 使用 TanStack Query；有 OpenAPI 时可采用生成客户端。不要为无后端的扩展引入这些依赖。
- 测试选择与配置见 [testing.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/testing.md)。

## 上下文职责

| 上下文 | WXT 典型入口 | 边界 |
|---|---|---|
| popup / options | `entrypoints/popup/`、`entrypoints/options/` | React 页面；popup 关闭后不能承担持续任务 |
| background | `entrypoints/background.ts` | 非持久 service worker，事件响应、特权操作和跨上下文协调，无 DOM |
| content script | `entrypoints/<name>.content/` | 默认 isolated world；与宿主共享 DOM，JS 全局隔离，可挂载 React UI |
| side panel（按需） | `entrypoints/sidepanel/` | 独立 UI；按实际 WXT 配置和权限核对 manifest |

- worker 状态应可从持久存储恢复或重新计算；允许事件内变量和可丢弃缓存，不依赖内存跨 worker 重启存活。事件监听在 WXT background 的 main 中同步注册，不能等异步初始化后才注册。
- 可跨挂起恢复的定时任务用 `chrome.alarms`，处理重建、重复触发和幂等；不依靠 `setInterval` 保持后台任务。
- Query 可用于 popup/options/side panel 或 content script 的 React UI；background 不复用 UI Query 缓存。Zustand 不复制 Query 中的服务端对象。
- 简单 popup/options 默认无需路由；多页导航确有需要时按设计采用。
- WXT content/background 入口的运行时副作用放在 main 中，避免构建期模块求值访问 DOM 或 browser API；HTML 页面的脚本沿用其运行时入口。共享模块不得通过副作用导入其他入口。
- `.output/`、`.wxt/` 是派生物，修正源码或配置后重新生成。

## 消息与请求

- 消息名称、payload、响应和错误集中定义；调用方复用，不散落裸 sendMessage。类型安全不能替代接收端的 Zod 校验。
- background 接收 content script 请求时，校验 sender、站点/操作范围及 payload；由 handler 构造允许的请求，不接受任意 URL 代理。
- 需集中鉴权、跨上下文协调或超出 popup 生命周期的操作交给 background；扩展 UI 在权限允许且设计明确时可以直接请求。content script 的跨域请求仍受宿主源约束。
- 持续通信按需用 Port，并定义断连、重连和取消；Port 不是后台永久存活保证。
- MAIN world 注入仅用于确需访问页面 JS 的场景；桥接消息视为不可信输入，不暴露凭据或任意特权操作。

## 存储

- 业务 key 用 `storage.defineItem` 集中定义，带 `local:` / `sync:` / `session:` 前缀；`managed:` 是企业策略只读区域。
- 需兼容旧数据的结构变更声明 version 和 migrations；既有无版本数据按 v1 处理，首次变更从 v2 迁移。迁移失败不得静默覆盖原数据。
- 跨上下文同步用 watch，并在 UI 卸载时取消监听；设计明确写入方，避免多个上下文读改写覆盖。
- Zustand persist 仅在确需持久化 UI 状态时适配 WXT storage；明确异步 hydration、watch 更新和写回防循环。不要同时维护两套迁移或持久化真源。
- token 等敏感会话数据优先 `session:`，禁止 `sync:`；确需持久化时在设计中说明原因，并限制 `local` 为 trusted contexts（`setAccessLevel`）。content script 通过受限消息调用能力，不读取凭据。
- `localStorage` 不承载扩展跨上下文状态：worker 无此 API，content script 的 DOM storage 属于宿主。

## 权限与内容脚本 UI

- permissions、host_permissions、匹配范围和 CSP 的增量必须有设计/已确认变更依据；按使用场景考虑 activeTab 或可选权限，覆盖拒绝、撤销后的反馈。
- 可执行逻辑随扩展打包；不引入远程代码加载或 eval 方案。生产构建的 manifest 是核对权限、入口及 CSP 的最终证据。
- 注入 React UI 默认使用 WXT shadow-root UI，样式和 portal container 指向 shadow root 内容器。卸载时清理 React root、事件、watch 和 observer，避免重复注入；确需 iframe 或宿主内联布局时由设计说明取舍。
- 通用 Query/Zod/Tailwind 模式仅在采用相应库时读 [frontend patterns](${CLAUDE_PLUGIN_ROOT}/guides/frontend/patterns.md)；交互 UI 的选择器读 [testid 规范](${CLAUDE_PLUGIN_ROOT}/guides/frontend/testid-standards.md)。

修改代码时遵循 [注释契约](${CLAUDE_PLUGIN_ROOT}/protocols/code-comment-contract.md)；完成前按 [validation.md](${CLAUDE_PLUGIN_ROOT}/guides/extension/validation.md) 验证。

库级事实变更时核对 [WXT Storage](https://wxt.dev/storage.html)、[Content Scripts](https://wxt.dev/guide/essentials/content-scripts.html)、[Chrome Storage](https://developer.chrome.com/docs/extensions/reference/api/storage) 和 [跨域请求](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests)。
