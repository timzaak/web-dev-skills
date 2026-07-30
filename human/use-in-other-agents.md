# 在其它 AI 编程工具中使用 t-tools (Codex / ZCode)

本文说明如何把这个 Claude Code plugin 用在 Codex、ZCode 等**不支持 `claude --plugin-dir` 加载、但支持 skill 目录**的 AI 编程工具里。

它解决的核心问题是:本插件的正式入口是 `/t-tools:t-*`,依赖 Claude Code 的插件加载机制。其它工具没有这套机制,但它们都从统一的 skill 目录 `~/.agents/skills/` 发现并加载 skill(这是 [open agent skills 生态](https://github.com/vercel-labs/skills) 的约定)。因此适配方式不是把整个插件搬进 skill 目录,而是在 `~/.agents/skills/` 下放一个**薄路由 skill**,把 `/t-tool <skill-name>` 路由到本仓库 `git clone` 后的 `skills/<skill-name>/SKILL.md`。

## 为什么这样设计

- **单一事实源**:本仓库的 skill、agent、protocol、guide 只维护一份,通过 `git pull` 更新。`~/.agents/skills/t-tool/` 只是入口,几乎不需要改。
- **路径透传**:dispatcher 把仓库根目录作为 `${CLAUDE_PLUGIN_ROOT}` 注入,skill 体内的 `agents/`、`protocols/`、`guides/`、`templates/`、`scripts/` 等同级资源继续按原本的语义路径解析,不依赖插件加载机制。
- **触发稳定**:`description` 里写明 `/t-tool`,模型在用户输入斜杠命令时能稳定识别并调用。

## 前置条件

- 已 `git clone` 本仓库到某个固定路径,例如 `~/code/skills` 或 `C:/code/ai/skills`
- 目标 AI 工具支持从 `~/.agents/skills/` 加载 skill(Codex、ZCode、Cursor、Cline 等都支持)
- 已配置 Context7 MCP(见下文 [安装 Context7](#安装-context7))

## 安装步骤

### 1. 克隆本仓库到固定路径

```bash
git clone <repo-url> ~/code/skills
```

后续所有 `${CLAUDE_PLUGIN_ROOT}` 引用都会指向这个路径,所以选一个不会经常移动的位置。下面用 `<CLONE_PATH>` 代指它。

### 2. 创建 dispatcher skill

新建 `~/.agents/skills/t-tool/SKILL.md`,内容如下。把 `<CLONE_PATH>` 替换成上一步的克隆路径(Windows 下用正斜杠 `/`,例如 `C:/code/ai/skills`),把 `<Agent>` 替换成你用的工具名(如 `Codex`、`ZCode`):

````markdown
---
name: t-tool
description: Dispatcher for the t-tools plugin. Use when the user types "/t-tool <skill-name>".
---

# t-tool — t-tools Plugin Dispatcher

Entry point for the **t-tools** plugin at `<CLONE_PATH>`. That plugin is not on <Agent>'s load path, so its sub-skills are not directly invokable — this dispatcher loads and runs them.

## Invocation

```
/t-tool <skill-name> [args...]
```

No argument → run `ls <CLONE_PATH>/skills/` to list available sub-skills, then stop.

## Procedure

1. Read `<CLONE_PATH>/skills/<skill-name>/SKILL.md`. Missing → list the directory and stop.
2. Execute it as the active skill. Substitute `${CLAUDE_PLUGIN_ROOT}` with `<CLONE_PATH>`; sibling resources (`agents/`, `protocols/`, `guides/`, `templates/`, `scripts/`) resolve under the same root.
3. Complete its full flow; do not re-dispatch.
````

`description` 是触发条件,保留 `/t-tool` 字样即可。

### 3. 配置 Context7 MCP

见下文 [安装 Context7](#安装-context7)。Context7 是 `requiredMcpServers`,不配会导致 `t-design`、`t-run` 等阶段失败。

## 调用方式

Claude Code 里的 `/t-tools:t-<skill>` 在 Codex / ZCode 里对应 `/t-tool <skill>`。差别只是把命名空间分隔符 `:` 改成空格,参数完全透传:

| Claude Code | Codex / ZCode |
| --- | --- |
| `/t-tools:t-prd user-management` | `/t-tool t-prd user-management` |
| `/t-tools:t-prd-check user-management` | `/t-tool t-prd-check user-management` |
| `/t-tools:t-run user-management --phase backend` | `/t-tool t-run user-management --phase backend` |
| `/t-tools:t-super-run user-management --phase backend` | `/t-tool t-super-run user-management --phase backend` |

不带参数运行 `/t-tool` 会列出本仓库 `skills/` 下所有可用子 skill。

## 工作目录约定

dispatcher skill 不改变本插件对目标项目的运行时约定。在**目标项目根目录**下启动 Codex / ZCode,确保以下目录存在:

- `docs/` — 正式产品文档
- `.ai/` — 工作流产物(PRD 草稿、设计、任务、预览等)

这些路径由 skill 体内的 protocol 约定,与具体 AI 工具无关。

## Sub-Agent 在 ZCode/Codex 中的加载

ZCode / Codex 等非 Claude 工具通常不会像 `claude --plugin-dir` 那样自动注册 `agents/*.md`。本插件不要求用户额外配置 agent 注册；调用子 agent 的 skill 会按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 显式注入角色规范。

只要 dispatcher 注入的 `${CLAUDE_PLUGIN_ROOT}` 指向本仓库克隆位置，且仓库内 `agents/` 目录存在，支持 `~/.agents/skills/` 与子 agent/任务委派能力的工具即可按同一规则运行。

## 安装 Context7

Context7 提供第三方库的最新版本文档,在 `t-design`、`t-run` 等阶段会被查询。它是一个基于 Streamable HTTP 的 MCP server,通用配置要素:

- Server URL:`https://mcp.context7.com/mcp`
- 鉴权:通过 HTTP header `CONTEXT7_API_KEY` 传入你在 [context7.com](https://context7.com) 申请的 API key

**OpenAI Codex**(CLI / App / VS Code 扩展共享同一份配置):

编辑 `~/.codex/config.toml`:

```toml
[mcp_servers.context7]
url = "https://mcp.context7.com/mcp"
http_headers = { "CONTEXT7_API_KEY" = "ctx7sk-..." }
```

或在 Codex App 里 Settings → MCP Servers → + Add servers。

**其它客户端**(Cursor / Cline / Claude Code / Gemini CLI / ZCode 等):

各客户端的 MCP 配置位置和写法不同,且会随版本变化。请以 Context7 官方文档为准,而不是依赖本文档的示例:

- Context7 官方仓库:<https://github.com/upstash/context7>
- 各客户端配置索引:<https://context7.com/docs>(左侧 Clients 章节,按客户端查找最新写法)
- Codex 专页:<https://context7.com/docs/clients/codex>

配置后重启客户端,在会话里触发一次库文档查询验证连通性。

## 验证

完成上面三步后,在任意目标项目目录下运行:

```
/t-tool
```

应该列出 `skills/` 下所有 `t-*` skill。再试一个轻量命令:

```
/t-tool t-decision demo-feature
```

如果它能正常读取 `<CLONE_PATH>/skills/t-decision/SKILL.md` 并按其流程执行,说明 dispatcher、`${CLAUDE_PLUGIN_ROOT}` 替换和 Context7 都已就绪。

## 已验证可用的工具

- **ZCode** — 直接支持 `~/.agents/skills/` 加载 skill 和 MCP 配置。
- **OpenAI Codex**(CLI / App)— 支持 `~/.agents/skills/` 加载 skill,以及 `~/.codex/config.toml` 的 MCP 配置。

其它从 `~/.agents/skills/` 加载 skill 的工具(Cursor、Cline 等)原理相同,但未在本项目逐个验证。

## 维护与更新

- **更新本插件**:`cd <CLONE_PATH> && git pull`
- **dispatcher skill 几乎不需要改动**,除非本仓库 `skills/` 目录结构发生破坏性变更
- **Context7 连接失败**:先检查 `http_headers` 里的 API key 是否有效,再核对官方文档里该客户端的最新配置写法
