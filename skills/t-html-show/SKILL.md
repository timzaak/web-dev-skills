---
name: t-html-show
description: Generate or update an HTML Preview for a Markdown document.
argument-hint: "[document-path]"
allowed-tools:
  - Read
  - Agent
  - Bash
---

# 文档 HTML Preview 生成

将一个 Markdown 文档交给 `html-show` subagent，生成或更新 `.ai/preview/` 下的可视化审阅页。

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`。
内容、路径、检查与打开规则统一以 `${CLAUDE_PLUGIN_ROOT}/protocols/html-show-contract.md` 为准；PRD 额外遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md`。本 skill 只负责入口校验、委派和结果收口，不重复定义 Preview 规则。

## 使用方式

```bash
/t-html-show <path-to-markdown>
```

参数必须是已存在的 Markdown 文件路径，直接来自 `$ARGUMENTS`；拒绝空参数、非文件路径和包含 `..` 的路径。

不要用本命令创建或修改源文档：

- PRD 创建或更新使用 `/t-prd`
- PRD 完整性检查使用 `/t-prd-check`
- 需要改变文档语义时，先修改源文档，再重新生成 Preview

## 工作流程

1. 读取以下文件：
   - `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
   - `${CLAUDE_PLUGIN_ROOT}/protocols/html-show-contract.md`
   - `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`
   - `${CLAUDE_PLUGIN_ROOT}/agents/html-show.md`
   - PRD 输入额外读取 `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md`
2. 校验 `$ARGUMENTS`，确认源 Markdown 文件存在。
3. 按 `subagent-dispatch.md` 委派 `html-show`：将完整 agent 角色定义注入 prompt，并只追加本次源文档路径。
4. 检查 subagent 返回的 `status`、`preview_path` 和 `check_result`；失败时原样报告具体问题，不宣称已完成。
5. 默认不打开 Preview。报告路径和当前平台的打开命令；仅当用户明确要求打开时，按 `html-show-contract.md` 的 `Opening the Preview` 执行并确认结果。

最小委派上下文：

```text
使用 html-show 生成或更新 HTML Preview。
源文档: <document-path>
```

## 完成输出

向用户报告：

- `preview_path`
- `doc_type`
- `mode`: `create | update`
- `visualization_type`
- `check_result`
- 打开命令，以及外部依赖所需的安装、构建或启动命令（如有）

若 subagent 返回 `required_doc_updates`，明确说明 Preview 不能代替源文档承载这些语义变更。

## 失败条件

- 参数缺失、不是 Markdown 文件路径、包含 `..` 或源文件不存在
- agent 角色未注册或无法委派
- Preview 无法写入或机械检查无法通过
- 源文档、契约或用户最新意图冲突

发生失败时保留已生成文件，报告原因和路径；不得绕过契约或伪报成功。
