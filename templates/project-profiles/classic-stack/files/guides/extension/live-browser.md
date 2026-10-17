# 用户当前 Chrome 调试

扩展开发需要复现用户当前标签页、登录态、宿主网站或已安装扩展的交互时读取本页。统一采用 Google Chrome 官方维护的 **Chrome DevTools MCP + `--autoConnect`**；不为不同 AI 客户端另建浏览器桥接。可重复回归仍按 [测试指南](${CLAUDE_PLUGIN_ROOT}/guides/extension/testing.md) 使用独立 Chromium fixture。

## 接入

前置条件：本机 Node.js LTS/npm、Chrome 144+，MCP 进程与目标 Chrome 在同一台机器、同一用户环境运行。远程开发或 WSL 不假设可自动发现宿主 Chrome，先在 Chrome 所在环境验证连接。

1. 用户在日常使用的 Chrome 打开 `chrome://inspect/#remote-debugging`，启用远程调试。
2. 按客户端配置下面同一个服务，重启或重新加载客户端的 MCP。
3. 首次调用浏览器工具时，用户在 Chrome 中允许连接。工具可见不等于浏览器连接成功。

### Codex

```bash
codex mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest --autoConnect
```

### Claude Code

```bash
claude mcp add --scope user chrome-devtools -- npx -y chrome-devtools-mcp@latest --autoConnect
```

### ZCode

设置 → MCP 服务器 → 新建 → 完整配置，填入：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--autoConnect"]
    }
  }
}
```

已有同名服务时更新参数，不重复添加。Windows 客户端若无法直接启动 `npx`，改用 `command: "cmd"`、`args: ["/c", "npx", "-y", "chrome-devtools-mcp@latest", "--autoConnect"]`。首次安装可用 `@latest`；团队复用时记录验证过的服务版本，按需固定版本。

不得省略 `--autoConnect` 后把工具启动的独立 profile 当成用户浏览器。Chrome 136 起，旧的 `--remote-debugging-port` / `--remote-debugging-pipe` 启动参数不能用于默认用户数据目录；不要通过复制个人 profile 或改用临时 profile 声称已连接原现场。

## 确认现场与采集

先按 [现场证据契约](${CLAUDE_PLUGIN_ROOT}/protocols/extension-acceptance-contract.md) 确认任务输入、角色工具权限、记录内容和交接方式，再采集：

1. 使用 `list_pages` 找到任务给出的标签页；同名或多 profile 无法区分时返回主会话确认，不默认选第一个页面。
2. 按实际工具 schema 使用 `pageId` 或 `select_page` 选定目标；读取快照和截图，确认是已复现的页面状态。不要先导航或刷新丢失现场。
3. 读取与问题有关的 console 和 network 信息。未捕获复现前的日志时明确缺失，由开发角色在任务授权范围内复现后重新采集。
4. 核对实际扩展 ID、版本及加载产物。工具不能取得的事实由用户从扩展管理页提供，标注来源；不要仅凭构建成功推断浏览器已加载最新产物。

只采集任务相关内容；截图、日志和网络证据去除无关个人信息及凭据，不导出整份 cookie/profile。读取页面不需要安装、卸载其他扩展或扩大目标扩展权限。

## 扩展上下文与修复复核

| 观察对象 | 需要确认的覆盖边界 |
| --- | --- |
| 宿主页面 / content script | 页面快照可证明可见注入效果；页面 JavaScript 执行上下文不自动等同于 content script 隔离世界 |
| popup / options / side panel | 确认实际入口和可访问 target；把 popup URL 打开成标签页不能证明工具栏 popup 的关闭生命周期 |
| background service worker | 使用当前版本实际提供的 worker 工具/日志；拿不到目标 worker 时标记未验证，不能以宿主页面无报错代替 |

开发角色修复后先 build，再在用户当前 Chrome 重载对应开发扩展，必要时刷新宿主页面使 content script 更新，并核对新产物。服务版本支持且任务授权需要时，可开启 `--categoryExtensions` 使用扩展管理工具；否则由用户完成重载。该开关不属于默认只读接入配置。accept 只读消费证据，不执行重载、安装、业务点击或存储修改。

按原复现步骤采集修复后证据，并运行受影响的独立回归。调试连接可能影响 worker 挂起；生命周期验收须另外取得设计要求的真实挂起/恢复证据，不能将持续调试中的正常运行当作证明。

## 失败与恢复

Chrome 版本不足、授权被拒绝、服务不可用、标签页关闭或连接中断时，保留已有证据并返回具体缺口。恢复后重新列举页面并核对扩展及现场状态，不复用过期 page ID；非幂等业务操作不得自动重放。只断开本次调试连接，不关闭用户浏览器或清除其 profile。下游判定和重复验收遵循现场证据契约。

## 官方资料

连接参数、工具或客户端配置与本页不符时读取对应官方资料，再按实际版本调整；不得假定全部工具在所有版本均存在。

- [Chrome 自动连接](https://developer.chrome.com/docs/devtools/agents/use-cases/auto-connect)
- [Chrome DevTools MCP 与运行要求](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- [工具与扩展能力](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/tool-reference.md)
- [客户端配置与 Windows 配置](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/client-configurations.md)
- [Chrome 远程调试启动参数变更](https://developer.chrome.com/blog/remote-debugging-port)
- [Codex MCP](https://developers.openai.com/codex/mcp)
- [ZCode MCP](https://zcode.z.ai/cn/docs/mcp-services)
