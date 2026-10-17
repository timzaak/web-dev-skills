---
name: t-init
description: Connect an existing project to generic workflow conventions, optionally adding Web Demo infrastructure; does not scaffold an application or select its technology stack.
argument-hint: "[--web-demo]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
  - Bash
---

# 项目工作流接入

在当前已有项目中建立最小工作流入口；不生成应用骨架，不选择语言、架构或测试框架。只接受空参数或 --web-demo，其他旧初始化参数给出新用法并停止。

1. 先读 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`、目标项目 AGENTS.md、真实脚本、配置和 CI。没有项目实现或已选骨架时，说明应先确定项目方案；不自动创建模板工程。
2. 读取 `${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/scripts-template.md`，从真实入口生成或增量更新 scripts/index.md。写明命令、cwd、前置条件、结果与清理位置；没有的入口标明缺口，不生成虚构命令。t-push 需要项目本地 scripts/ci.py；已有明确 CI 门禁时可生成调用这些真实命令的薄入口，未确定时只报告缺口，不自行增加检查策略。
3. 根 AGENTS.md 仅增补读取 scripts/index.md 与项目规范索引的入口；已有约束、用户内容与忽略规则保留，不覆盖重写。只有用户已确认的项目实践可成为执行约束，候选知识保持草稿。
4. --web-demo 时读取 `${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/demo-template.md`，建立独立 demo/ 测试包；读取 `${CLAUDE_PLUGIN_ROOT}/skills/t-init/references/unified-logger-package-template.md` 配置日志依赖。URL、身份 fixture、启停与清理来自项目事实，无默认应用端口或数据库；模板只取适用部分。对登录/数据准备缺口先询问，不生成假业务故事。
5. 按需复制 Web Demo runner、批次 runner、失败摘要、调试/日志清理工具及其 lib 依赖到目标项目 scripts/。不复制任何预设应用启停实现。环境由项目本地 demo-start.py、demo-health.py、demo-stop.py 管理；已有环境或 fixture 管理时用 --no-auto-env。运行要求见 `${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md`。
6. 核对索引与实际入口一致。Web Demo 配置运行安装、lint、type-check 和独立 smoke（仅测试浏览器/日志通路）；真实故事另经 web-demo 阶段验收，不能以 smoke 代替。依赖工具缺失或执行失败明确标未验证，不能报告接入完全成功。

完成时报告变更、验证与缺口；重复执行只补缺失入口并复核已有配置。写入失败保留用户文件，报告失败位置并从同一命令恢复。领域知识沉淀的后续设计见仓库 human/generalization-plan.md；该方案尚未作为新命令实现。
