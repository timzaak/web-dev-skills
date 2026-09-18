---
name: t-how
description: Interactive guide that teaches how to use the t-tools plugin. Explains the Decision -> PRD/Tech Research -> Design -> Task -> Run -> Demo -> Release workflow, maps the user's goal or question to the right /t-tools:t-* entry command, and shows preconditions and next steps. Use when the user types "/t-tools:t-how" or asks how this plugin works, which command fits a goal, or how stages connect. Teaching only; never executes stages or writes target-project files.
argument-hint: "[主题或问题]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
---

# 教用户使用 t-tools

交互式使用向导：弄清用户想做什么，讲解对应工作流，并给出应执行的入口命令。只讲解和指路，不执行任何 `t-*` 工作流，不读写目标项目文件，也不代替用户做检查或初始化。

## 参数

```text
/t-how [主题或问题]
```

主题可省略。省略时先展示主链路和常见场景，用 AskUserQuestion 让用户选择（选项来自场景路由表），或自由描述目标。

输出语言跟随用户输入。

## 主链路

```text
t-decision -> t-prd / t-tech-research（无固定顺序，进设计前收敛）
-> t-design -> t-task -> t-run / t-super-run
-> t-web-demo-* / t-flutter-demo-* -> t-prd-publish -> t-push -> t-release
```

`t-prd-check`、`t-design-check`、`t-task-check` 是可选质量检查。phase 顺序：Web 为 `backend -> frontend -> web-demo`，Flutter 为 `backend -> flutter -> flutter-demo`。

## 场景路由

按用户目标匹配下表，讲解时给出命令、关键前置条件和下一步。匹配多个场景时全部列出，让用户确认顺序。

| 用户目标 | 入口命令 | 说明 / 下一步 |
|---|---|---|
| 从零做一个新功能 | `/t-tools:t-decision <feature>` | 立项门禁；按主要未知项进入 PRD 或技术预研 |
| 技术可行性、依赖、成本不明 | `/t-tools:t-tech-research <feature>` | 结论改变产品语义时重跑 `t-prd` |
| 写 / 更新 PRD 草稿 | `/t-tools:t-prd <feature>` | 只写 `.ai/prd` 候选草稿 |
| 把已验收需求转正 | `/t-tools:t-prd-publish <feature>` | 长期事实合并回 `docs/` |
| 技术设计 | `/t-tools:t-design <feature>` | 主文档 + 分端设计，后端契约先行 |
| 任务拆解 | `/t-tools:t-task <feature> --phase <phase>` | 生成 item 级任务 |
| 实现 + 测试 | `/t-tools:t-run <feature> --phase <phase>` | 串行执行 item |
| Chrome 扩展开发 | `/t-tools:t-design <feature>`，再 `t-task` / `t-run --phase extension` | 先按 [extension 初始化指南](${CLAUDE_PLUGIN_ROOT}/guides/extension/initialization.md) 建 WXT 工程；扩展不走 t-super-run，t-init 尚无扩展模板；浏览器演示用 web-demo |
| 强模型单会话实现 | `/t-tools:t-super-run <feature> --phase <phase>` | 合并规划与执行；`--phase` 必填 |
| Web Demo / E2E | `/t-tools:t-web-demo-run <file>` 或 `/t-tools:t-web-demo-run-all` | 之后 `/t-tools:t-web-demo-accept <role>` |
| Flutter Demo | `/t-tools:t-flutter-demo-run <file> --device <id>` 或 `/t-tools:t-flutter-demo-run-all` | 之后 `/t-tools:t-flutter-demo-accept <domain\|all>` |
| 提交推送 | `/t-tools:t-review`、`/t-tools:t-simplify`，再 `/t-tools:t-push` | review 只报告，发现缺陷先修复；push 会清理注释并跑受影响 CI |
| 发版 | `/t-tools:t-release [版本号]` | semver 不带 `v`，git tag 带 `v` |
| 写项目教程 / 文档 | `/t-tools:t-doc [名称]` | 不用于 PRD 和技术设计 |
| 审计上下文 / 结构漂移 | `/t-tools:t-dream [feature]` | 默认只读；PRD 治理加 `--govern-prd` |
| Figma 还原 | `/t-tools:t-figma-assets`，再 `/t-tools:t-figma-impl` | 动效 `t-figma-ux` |
| 新项目脚手架 | `/t-tools:t-init <project-name>` | Rust + React 全栈骨架 |

表外还有 `t-html-show` 等辅助命令：用 Glob 列出 `${CLAUDE_PLUGIN_ROOT}/skills/`，读对应 `SKILL.md` 开头确认职责后再讲解。

## 讲解方式

- 先给最短可用路径（1-3 条命令），再按需展开阶段细节；不要一次性铺开全部工作流。
- 涉及前置条件时（`docs/`、`.ai/` 目录，context7 MCP，Figma MCP，`--device` 等），随命令一起说明，但不要代替用户检查或创建。
- 用户想理解整体设计思路（skill、subagent、protocol 如何协同）时，读取 `${CLAUDE_PLUGIN_ROOT}/human/structure.md` 再讲解。
- 用户要完整命令示例时，指向仓库 README 的“快速上手”章节。
- 用户在 Codex / ZCode 等不支持 `claude --plugin-dir` 的工具里时，说明命令形式对应 `/t-tool <skill-name>`，见 `${CLAUDE_PLUGIN_ROOT}/human/use-in-other-agents.md`。

## 失败处理

- 匹配不到场景：列出场景路由表的目标列让用户选择，或请用户换个说法描述目标。
- 用户问的命令不存在：用 Glob 列出实际可用的 skill，纠正命令名。
- 用户要求直接开工：说明本 skill 只负责讲解，给出应执行的命令，由用户显式触发。
