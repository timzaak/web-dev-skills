---
name: t-doc
description: |
  Generate project tutorial documentation that reads like a human wrote it, not like AI output.
  Scans the codebase, extracts architecture/APIs/config/deployment details, and writes
  structured tutorial docs in the project's documentation target, preferring an existing
  docs-web site over docs/tutorials/. Use this skill whenever the user asks to
  write project docs, tutorials, getting-started guides, API references, deployment guides,
  onboarding docs, or any kind of project walkthrough. Also trigger when they say "write
  documentation", "generate docs", "create a tutorial", "onboarding guide", "write a guide",
  or want help producing readable documentation for a project or module — even if they don't
  explicitly say "tutorial."
argument-hint: "[项目或模块名]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
  - Bash
  - Agent
---

# 写项目教程文档

扫描代码库，提取架构、API、配置、部署等信息，写给新人能读懂的项目教程。文档要像工程师写的，不像自动生成的 API 文档。

## 使用场景

- 用户执行 `/t-doc [名称]`
- 用户要写项目文档、教程、上手指南、README 教程、onboarding 文档
- 用户需要面向新人的项目或模块 walkthrough

不要用于 PRD、技术设计、纯 API schema 自动生成，或只改某个文档小段落的任务。

## 参数和语言

命令格式：

```text
/t-doc [项目或模块名]
```

`名称` 必填，1-50 字符，只允许英文、数字、连字符、下划线。不合法就终止，并提示：

```text
请提供合法的名称。例如：/t-doc my-project
```

输出语言跟随用户输入；用户没明确指定时默认中文。

## 教程位置判定

写作前先在项目根目录判定教程目标，后续扫描、已有文档检查、写入和验证都使用同一个目标：

1. 如果存在 `docs-web/`，优先把教程集成到该文档站点中，不再写入 `docs/tutorials/`。
2. 读取 `docs-web/README.md`、`package.json`、站点配置、内容源配置、路由和已有页面，识别真实的内容目录、文件格式、语言结构与导航方式。例如内容可能位于 `docs-web/content/docs/`，但不要只凭目录名硬编码。
3. 沿用站点已有约定：使用 `.md` 或 `.mdx`，放进现有教程分组或文档内容层级；多语言站点按现有语言目录组织；同步更新 `meta.json`、sidebar、nav、索引页等导航入口，确保教程能通过 Web 页面访问和发现。
4. `docs-web/` 存在但无法从配置和现有内容确认内容源或路由规则时，列出已识别的候选位置并询问用户，不要静默回退到 `docs/tutorials/`。
5. 只有项目根目录不存在 `docs-web/` 时，才使用 `docs/tutorials/` 和下面的 Markdown 默认结构。

目标确定后检查其中是否已有对应教程。若存在，先告诉用户已有内容，询问覆盖还是增量更新。

- 覆盖：重写目标教程。
- 增量更新：先读已有文档，只补充或修正变化部分。

## 信息收集

动笔前先扫描项目。优先看这些来源：

| 来源 | 关注点 |
|------|--------|
| `README.md`, `CLAUDE.md` | 项目定位、技术栈、运行方式 |
| `package.json`, `Cargo.toml`, `pyproject.toml` | 依赖和版本 |
| `src/`, `app/`, `lib/` 入口文件 | 模块结构、路由、核心抽象 |
| `docs/`, `guides/`, `protocols/` | 现有文档和规范 |
| `docs-web/` 的配置、内容与导航文件 | 文档站内容源、格式、语言、路由和导航约定 |
| `docker-compose.yml`, `Dockerfile` | 部署方式 |
| `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile` | CI/CD |
| `.env.example`, `config/` | 配置项 |
| 数据库 migration 文件 | 数据模型 |

Glob 搜索要避开依赖目录。优先用明确路径，例如 `.github/workflows/*.yml`、`Dockerfile`、根目录下的 compose 文件；必须用 `**` 时，用 `path` 限定范围，避免扫到 `node_modules`、`vendor`、`.venv`。

按项目规模选择扫描深度：

- 小项目（少于 30 个源文件）：直接用 Glob 和 Grep 全扫。
- 中大项目（30-200 个源文件）：先读入口文件和 README 建骨架，再按模块深入。
- 大项目（超过 200 个源文件）：先让用户指定覆盖范围，不要一次写完整项目。

扫完先给用户摘要：项目一句话、关键模块、还缺什么信息。连入口文件都找不到时，先问用户再继续。

## 输出结构

不存在 `docs-web/` 时，默认写到：

```text
docs/tutorials/
├── index.md
├── getting-started.md
├── architecture.md
├── api-reference.md
├── configuration.md
└── deployment.md
```

按项目实际裁剪。没有 API 层就不写 `api-reference.md`；部署只是 `git push` 的话，放在 `getting-started.md` 末尾即可。

存在 `docs-web/` 时，章节目标相同，但输出路径、扩展名和层级跟随站点已有约定。不要强制创建 `tutorials/` 子目录或 `index.md`；如果站点用元数据生成教程入口和顺序，就更新对应元数据。如果站点有多语言结构，只生成用户要求的语言；用户未指定且站点已有多语言版本时，先在大纲中说明准备生成哪些语言。

具体章节骨架见 [references/doc-templates.md](${CLAUDE_PLUGIN_ROOT}/skills/t-doc/references/doc-templates.md)。

## 写作要求

写作前读取 [references/writing-style.md](${CLAUDE_PLUGIN_ROOT}/skills/t-doc/references/writing-style.md)。每章写完后也按里面的自检清单检查一遍。

核心要求：

- 直接说事，不写"本文将""让我们"。
- 命令、配置、请求示例必须来自实际代码或项目文件，不能编。
- 架构说明要有判断：说明为什么这样选，必要时指出取舍。
- 代码示例要能复制运行，不用伪代码和占位 API key。
- 只在流程图能明显降低理解成本时使用 Mermaid。
- 不写空洞总结，不堆加粗标题、排比、口号和装饰性 emoji。

## 工作流程

- 目标判定：按“教程位置判定”选定 `docs-web/` 的实际内容源或 `docs/tutorials/`。
- 信息收集：按上面的来源扫描，用批量搜索建立项目事实；使用 `docs-web/` 时同时确认页面格式、路由、导航和验证命令。
- 确认大纲：告诉用户准备写哪些章节、各章覆盖什么，等用户确认或调整。
- 逐章编写：确认后按章节写入目标目录。
- 自检修订：按 [references/writing-style.md](${CLAUDE_PLUGIN_ROOT}/skills/t-doc/references/writing-style.md) 检查所有文件，改掉 AI 味、空话和不可验证内容；修订只动文风，不新增项目文件里不存在的事实，也不丢仍然成立的主张；使用 `docs-web/` 时运行站点已有的类型检查或构建命令，确认页面可生成且导航可达。

不要跳过大纲确认。先确认再写，避免整套文档返工。

## 逐章编写

推荐顺序：

- `index.md`
- `getting-started.md`
- `architecture.md`
- `api-reference.md`（如果需要）
- `configuration.md`（如果需要）
- `deployment.md`（如果需要）

可以用 subagent 分章写；具体调用按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 执行。每个 subagent 必须拿到：

- 扫描阶段得到的项目上下文，不要让它重新猜。
- 本章目标、输出文件和需要读取的源文件路径。
- [references/doc-templates.md](${CLAUDE_PLUGIN_ROOT}/skills/t-doc/references/doc-templates.md) 中对应章节的骨架。
- [references/writing-style.md](${CLAUDE_PLUGIN_ROOT}/skills/t-doc/references/writing-style.md) 的风格要求和自检清单。
