# 项目路由层模板与产物规则

t-init 建立或更新项目路由层时读取。路由层把工作流入口落进项目，但不复制插件正文：dispatcher 与索引只引用单一事实源（已验证的 t-tools 源工作树），维护规则见 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`。

## 产物

| 目标文件 | 来源与处理 |
| --- | --- |
| `.agents/skills/t-tool/SKILL.md` | 按下文 dispatcher 模板逐字生成，不含任何本机绝对路径 |
| `.claude/skills/t-tool/SKILL.md` | 同一模板的第二份副本，供未装插件的 Claude Code 会话发现；两份内容必须一致 |
| `.agents/guides/index.md` | 按下文索引模板生成；生成块条目由适用性规则结合项目事实选定 |
| `.agents/t-tools-source.json` | `{"root": "<绝对路径，正斜杠>", "revision": "<完整 commit>"}`，来自 `${CLAUDE_PLUGIN_ROOT}/scripts/resolve-ttools-source.py` 的输出；本机文件，不提交 |
| 根 `.gitignore` | 增补 `.agents/t-tools-source.json` 一行；已有规则保留，项目没有 `.gitignore` 时新建 |

项目已有 skill 目录约定或用户指定其他路由层位置时沿用实际位置，在收尾报告中记录偏差。

## dispatcher 模板

两处副本均按以下内容逐字生成：

````markdown
---
name: t-tool
description: Dispatcher for the t-tools plugin. Use when the user types "/t-tool <skill-name>".
---

# t-tool — t-tools Project Routing Entry

Thin routing entry installed by t-init. It does not copy plugin content; it resolves the single source root and runs the skill there.

## Invocation

```
/t-tool <skill-name> [args...]
```

No argument → run `ls <SOURCE_ROOT>/skills/` to list available sub-skills, then stop.

## Source Resolution

Resolve `<SOURCE_ROOT>` in this order; the first hit wins:

1. `${CLAUDE_PLUGIN_ROOT}` — defined when the t-tools plugin is loaded in the current session.
2. `T_TOOLS_ROOT` environment variable — absolute path to a clone of the t-tools repository.
3. `.agents/t-tools-source.json` in the project root — `{"root": "<absolute path>"}` recorded by t-init on this machine.
4. No hit → stop and tell the user: clone the t-tools repository, then either set `T_TOOLS_ROOT` or write `.agents/t-tools-source.json` with `{"root": "<clone path>"}`. That file is gitignored and per machine.

## Procedure

1. Read `<SOURCE_ROOT>/skills/<skill-name>/SKILL.md`. Missing → list the directory and stop.
2. Execute it as the active skill. Substitute `${CLAUDE_PLUGIN_ROOT}` with `<SOURCE_ROOT>`; sibling resources (`agents/`, `protocols/`, `guides/`, `templates/`, `scripts/`) resolve under the same root.
3. Complete its full flow; do not re-dispatch.
````

## 索引模板与适用性规则

`.agents/guides/index.md` 结构：

````markdown
# 工程指南路由索引

由 t-init 生成的路由层：正文不复制，条目指向 t-tools 单一事实源中的指南。`<SOURCE_ROOT>` 按 `.agents/skills/t-tool/SKILL.md` 的 Source Resolution 解析；工作流命令经 `/t-tool <skill-name>` 调用（无参列出全部）。

<!-- t-init:begin source=<revision 前 12 位> -->
## 适用指南

| 话题 | 入口 | 何时读取 |
| --- | --- | --- |
| （按适用性规则生成的行） | | |

<!-- t-init:end -->

## 项目自订条目

t-init 重跑只更新上方生成块；项目专属指南在本节维护。
````

生成块行按以下规则从已验证源的 `guides/` 真实文件选定，未选中的域不列：

| 指南域 | 入口 | 适用条件（项目事实） | 何时读取 |
| --- | --- | --- | --- |
| core | `<SOURCE_ROOT>/guides/core/index.md` | 恒选 | 开发、测试与验收前读质量与环境分层 |
| product | `<SOURCE_ROOT>/guides/product/index.md` | 存在 `docs/prd/`、`docs/user-stories/` 或 `.ai/prd/` | 写 PRD 或用户故事前 |
| web-demo | `<SOURCE_ROOT>/guides/web-demo/index.md` | 存在 `demo/` 或 Playwright 配置/依赖 | demo 测试维护、失败修复前 |
| figma | `<SOURCE_ROOT>/guides/figma/index.md` | 存在 Figma 工作流痕迹或用户明确说明 | Figma 资产下载、重建前 |

项目事实不足以判定某域适用时，该行列出并标注待确认，不默认勾选也不静默省略。源中不存在的指南文件不得生成条目。

## 幂等与冲突

- 重跑时 dispatcher 副本与模板输出不一致则报告差异并保留现有文件，不覆盖；用户删除该文件后重跑才会重新生成。两份副本之间不一致时以模板输出为准报告差异。
- 索引重跑只替换 `t-init:begin`/`t-init:end` 之间内容，注释外的用户内容保留。文件存在但没有标记注释时报告冲突，不覆盖。
- `.agents/t-tools-source.json` 重跑时用最新解析结果覆盖刷新。
- 源验证失败时不写任何路由层文件，报告缺口并询问源码路径；确认后从本步骤恢复。
