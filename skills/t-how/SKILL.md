---
name: t-how
description: Interactive guide that teaches how to use the t-tools plugin. Explains the Decision -> PRD/Tech Research -> Design -> Super Run -> Demo -> Release workflow, maps the user's goal or question to the right /t-tools:t-* entry command, and shows preconditions and next steps. Use when the user types "/t-tools:t-how" or asks how this plugin works, which command fits a goal, or how stages connect. Teaching only; never executes stages or writes target-project files.
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
-> t-design -> t-super-run
-> t-web-demo-* -> t-prd-publish -> t-push -> t-release
```

`t-prd-check`、`t-design-check`、`t-task-check` 是可选质量检查。阶段启用与顺序从 task-phase-execution 协议读取。

## 场景路由

按用户目标匹配下表，讲解时给出命令、关键前置条件和下一步。匹配多个场景时全部列出，让用户确认顺序。

讲解 `--phase <phase>` 可选值或启用条件时，读取 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的 Phases；只展示与用户场景相关的阶段，参数说明不展开完整枚举。

| 用户目标 | 入口命令 | 说明 / 下一步 |
|---|---|---|
| 从零做一个新功能 | `/t-tools:t-decision <feature>` | 立项门禁；按主要未知项进入 PRD 或技术预研 |
| 技术可行性、依赖、成本不明 | `/t-tools:t-tech-research <feature>` | 结论改变产品语义时重跑 `t-prd` |
| 写 / 更新 PRD 草稿 | `/t-tools:t-prd <feature>` | 只写 `.ai/prd` 候选草稿 |
| 把已验收需求转正 | `/t-tools:t-prd-publish <feature>` | 长期事实合并回 `docs/` |
| 技术设计 | `/t-tools:t-design <feature>` | 主文档 + 真实模块设计，契约来源明确 |
| 实现 + 测试 | `/t-tools:t-super-run <feature> --phase <phase>` | 合并任务规划与执行；`--phase` 必填，每次只执行一个 phase |
| Web Demo / E2E | `/t-tools:t-web-demo-run <file>` 或 `/t-tools:t-web-demo-run-all` | 之后 `/t-tools:t-web-demo-accept <role>` |
| 提交推送 | `/t-tools:t-review`、`/t-tools:t-simplify`，再 `/t-tools:t-push` | review 只报告，发现缺陷先修复；push 运行项目实际 CI |
| 发版 | `/t-tools:t-release [版本号]` | semver 不带 `v`，git tag 带 `v` |
| 给插件新增或修改 skill | `/t-tools:t-skill [名称或能力描述]` | 只操作插件仓库自身，不用于目标项目业务开发 |
| 在目标项目内创建或更新 skill | `/t-tools:t-skill --project [名称或能力描述]` | 按项目运行时落位 `.claude/skills/` 或 `.agents/skills/`；feature 中已规划的 skill 交付物走 `t-super-run` 对应 phase |
| 写项目教程 / 文档 | `/t-tools:t-doc [名称]` | 不用于 PRD 和技术设计 |
| 审计上下文 / 结构漂移 | `/t-tools:t-dream [feature]` | 只读；报告可含 PRD 治理建议，不执行写入 |
| 阶段收口一致性 | `/t-tools:t-dream [feature] --phase <phase>` | 检查该交付阶段实现或 Demo 与 PRD / 用户故事的一致性；阶段取值见共享阶段执行协议 |
| Figma 还原 | `/t-tools:t-figma-assets` → `/t-tools:t-figma-impl` | 素材未就绪可先 impl，交付前补 assets 并绑定；动效精修用 `t-figma-ux` |
| 为产品图标 / logo 生成提示词 | `/t-tools:t-icon-prompt [icon-name]` | 问答产出提示词卡；只出提示词不生成图片，UI 图标集请用图标库 |
| 已有项目工作流接入 | `/t-tools:t-init [--web-demo]` | 记录真实运行入口，可选建立 Web Demo，不选择应用技术栈 |
| 拉取现成领域角色、实践或工程模板 | `python scripts/export-template.py list`，再显式 export | 读取 `${CLAUDE_PLUGIN_ROOT}/templates/index.md`，区分通用插件与固定版本的独立领域模板；本向导只讲解 |

表外还有 `t-html-show` 等辅助命令：用 Glob 列出 `${CLAUDE_PLUGIN_ROOT}/skills/`，读对应 `SKILL.md` 开头确认职责后再讲解。

## 讲解方式

- 先给最短可用路径（1-3 条命令），再按需展开阶段细节；不要一次性铺开全部工作流。
- 涉及前置条件时（`docs/`、`.ai/` 目录，context7 MCP，Figma MCP，`--device` 等），随命令一起说明，但不要代替用户检查或创建。
- 用户想理解整体设计思路（skill、subagent、protocol 如何协同）时，读取 `${CLAUDE_PLUGIN_ROOT}/human/structure.md` 再讲解。
- 用户需要原生产领域或 Java 后端模板时读取 `${CLAUDE_PLUGIN_ROOT}/templates/index.md`；维护 general 与 main 的同步时读取 `${CLAUDE_PLUGIN_ROOT}/human/merge-main.md`。不把模板中旧命令或 phase 当作当前通用插件已注册能力。
- 用户要完整命令示例时，指向仓库 README 的“快速上手”章节。
- 用户在 Codex / ZCode 等不支持 `claude --plugin-dir` 的工具里时，说明命令形式对应 `/t-tool <skill-name>`，见 `${CLAUDE_PLUGIN_ROOT}/human/use-in-other-agents.md`。

## 失败处理

- 匹配不到场景：列出场景路由表的目标列让用户选择，或请用户换个说法描述目标。
- 用户问的命令不存在：用 Glob 列出实际可用的 skill，纠正命令名。
- 用户要求直接开工：说明本 skill 只负责讲解，给出应执行的命令，由用户显式触发。
