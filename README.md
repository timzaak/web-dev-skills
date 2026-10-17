# T-Tools

[English](README.en.md)

面向实际项目的通用 Claude Code 工程工作流插件：可执行、可恢复、可验收。插件保留阶段编排、决策追踪、质量门禁和状态恢复；生产技术栈、架构与测试实践来自目标项目，不再内置领域预设。Web Demo 与 Figma 能力继续提供。

```text
Decision -> PRD / 技术预研 -> 设计 -> 实现 / 测试 -> 独立验收 -> 发布
```

先读 [结构说明](human/structure.md)，需求表达参考 [口述模板](human/speech-template.md)。泛化边界见 [generalization.md](human/generalization.md)，从项目沉淀领域知识的后续设计见 [方案](human/generalization-plan.md)；该方案尚未实现为新命令。

## 快速上手

命令均由用户显式触发；不知道入口时用 `/t-tools:t-how`。在已有项目根目录执行：

```text
/t-tools:t-init
/t-tools:t-decision sample-feature
/t-tools:t-prd sample-feature
/t-tools:t-design sample-feature
/t-tools:t-super-run sample-feature --phase implementation
/t-tools:t-prd-publish sample-feature
```

主要未知项是技术可行性、依赖或成本时先用 t-tech-research，与 PRD 在设计前收敛。只有不改变业务逻辑、产品规则、用户流程或验收目标的纯技术方案，才能从技术预研直接进入设计。

`t-prd-check`、`t-design-check`、`t-task-check` 是按风险使用的可选检查，不能替代实现后的 accept。

## 阶段与项目约束

当前支持通用 `implementation` 与可选 `web-demo`，启用条件、顺序、设计输入与角色映射仅在 [阶段执行协议](protocols/task-phase-execution.md) 维护。模块从真实项目结构确定，不按语言或目录预设交付端。

`t-super-run <feature> --phase <phase>` 每次只执行显式指定的一个阶段：主会话按 dev/test 角色完成工作，独立只读 accept 收口。中断后用同一命令从磁盘恢复；需要先审阅 item 计划时用 `t-task -> t-run`，两套状态独立。

项目 AGENTS.md、代码、配置和已确认文档决定工程规则。`t-init` 仅接入已有项目、建立真实运行说明，不生成应用骨架。项目 CI 由 `scripts/ci.py` 调用真实检查；缺失或失败时 push 停止。

旧领域命令和 phase 已移除，不做静默映射或旧状态自动迁移。已有项目保留原产物，按当前设计重新规划、核对证据后再执行。

## Web Demo

```text
/t-tools:t-init --web-demo
/t-tools:t-super-run sample-feature --phase web-demo
/t-tools:t-web-demo-run demo/e2e/<role>/<scenario>.e2e.ts
/t-tools:t-web-demo-run-all
/t-tools:t-web-demo-run-all continue
/t-tools:t-web-demo-accept <role>
```

初始化仅建立独立 Playwright 与日志通路，smoke 不代表真实故事已验收。URL、身份、数据隔离和清理由项目定义；自动环境管理需要项目本地 `scripts/demo-start.py`、`demo-health.py`、`demo-stop.py`（退出码 0 为成功）。fixture/外部管理环境时 runner 使用 `--no-auto-env`，不存在插件应用环境回退。细则见 [Web Demo 指南](guides/web-demo/index.md) 与 [修复契约](protocols/web-demo-run-repair-contract.md)。

## Figma

保留 `t-figma-assets`、`t-figma-impl`、`t-figma-ux`，面向目标项目现有文件完成素材处理、分块还原与动效精修；不指定生产框架。素材可延后准备，但交付前须绑定真实资产，页面由开发者验收。见 [Figma 指南](guides/figma/index.md) 和 [共享契约](protocols/figma-workflow-contract.md)。

## 质量链与辅助入口

提交前按 `t-review --fix -> t-simplify -> t-push` 收口；修复使证据失效时补跑回归和独立验收。review 默认只报告，存在未修复正确性问题不得 push；push 运行项目 CI 并支持远端失败恢复，见 [提交协议](protocols/push-execution-contract.md)。发布由 `scripts/release.py` 和 t-release 约束，语义版本不带 v，git tag 带 v。

| 目标 | 入口 |
| --- | --- |
| 理解工作流 | [t-how](skills/t-how/SKILL.md) |
| 立项与技术调研 | [t-decision](skills/t-decision/SKILL.md)、[t-tech-research](skills/t-tech-research/SKILL.md) |
| 需求与发布基线 | [t-prd](skills/t-prd/SKILL.md)、[t-prd-publish](skills/t-prd-publish/SKILL.md) |
| 设计与可选检查 | [t-design](skills/t-design/SKILL.md)、[t-design-check](skills/t-design-check/SKILL.md)、[t-prd-check](skills/t-prd-check/SKILL.md) |
| 计划与执行 | [t-super-run](skills/t-super-run/SKILL.md)、[t-task](skills/t-task/SKILL.md)、[t-run](skills/t-run/SKILL.md)、[t-task-check](skills/t-task-check/SKILL.md) |
| 正确性、清理与提交 | [t-review](skills/t-review/SKILL.md)、[t-simplify](skills/t-simplify/SKILL.md)、[t-push](skills/t-push/SKILL.md) |
| 上下文与实现一致性 | [t-dream](skills/t-dream/SKILL.md) |
| skill 创作 | [t-skill](skills/t-skill/SKILL.md)，项目内使用 --project |
| 文档与预览 | [t-doc](skills/t-doc/SKILL.md)、[t-html-show](skills/t-html-show/SKILL.md) |
| 图标提示词 | [t-icon-prompt](skills/t-icon-prompt/SKILL.md) |
| 接入与发版 | [t-init](skills/t-init/SKILL.md)、[t-release](skills/t-release/SKILL.md) |

## 可选领域模板

已移出的领域资产保留在 [templates/](templates/index.md)：[classic-stack](templates/project-profiles/classic-stack/index.md) 提供原 Rust/React、扩展、小程序、Flutter 与 Shopify 角色、实践、脚本和工程模板；[java-backend](templates/project-profiles/java-backend/index.md) 提供 java 分支的 Java/Spring Boot/Maven 后端内容。

```powershell
python scripts/export-template.py list
python scripts/export-template.py export classic-stack --output C:/code/ai/t-tools-classic
python scripts/export-template.py export java-backend --output C:/code/ai/t-tools-java
```

导出目录位于本仓库之外；--dry-run 只预览，重复执行不覆盖用户修改。导出会从模板固定提交取得配套共享运行时，再加入模板领域文件，得到可由 claude --plugin-dir 加载的独立插件。同一会话只选择通用插件或一份模板，不混用不同版本的 phase/state。模板默认不加载，不改变通用主链路；缺少来源提交时先 git fetch origin main 或 git fetch origin java。

## 持续维护

本分支持续合并 main 时，先读[合并 main 指南](human/merge-main.md)：分类保留通用更新、迁移领域变更、处理 modify/delete 冲突、单独推进模板来源版本，并验证两类运行时。

## 安装

```bash
git clone <repo-url>
cd /your-project
claude --plugin-dir /path/to/web-dev-skills
```

配置 Context7 MCP 供需要依赖文档的入口使用；Figma 工作流需要官方 Figma MCP，素材转换需要 ffmpeg/ffprobe、svgo 与 kyz，具体读取 [素材指南](guides/figma/assets.md)。Web Demo 需要 Python/uv、Node 与 Playwright 浏览器。工作流按需创建 .ai/ 与 docs/，不要求预建空状态。

其它 AI 工具的薄路由接入见 [跨工具使用说明](human/use-in-other-agents.md)。协议入口为 [protocols/index.md](protocols/index.md)。

## 使用本插件的项目

- [Herald](https://github.com/timzaak/herald) — 多租户认证与授权系统
- [RMQTT-Things](https://github.com/timzaak/rmqtt-things) — 物联网物模型管理平台
- [RWiki](https://github.com/timzaak/rwiki) — 基于 RAG 的知识库问答
- [OnceWise](https://github.com/timzaak/OnceWise) — 智能表单自动化助手

本项目迭代日志见 [linux.do](https://linux.do/t/topic/1988118/4)。
