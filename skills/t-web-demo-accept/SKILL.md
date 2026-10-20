---
name: t-web-demo-accept
description: Independently accept Web page demos against user stories and execution evidence, then summarize reports. Use after demo development; Chrome extension demos use t-extension-demo-accept.
argument-hint: "[测试文件路径|角色名|all]"
allowed-tools: [Read, Glob, Grep, Bash, Write, Agent]
---

# Web Demo 验收

## 范围与目标

按文件路径、目标项目实际角色目录或 `all` 解析 `demo/e2e/**/*.e2e.ts`；留空等同 `all`。批量排除 fixture/helper/template 与 `verification/`，所有参数均排除 `demo/e2e/extension/`，扩展故事提示使用 `/t-tools:t-extension-demo-accept`。显式初始化 verification 文件提示使用初始化验证入口，不作为故事验收。没有匹配故事文件时报告无可验收目标，不返回通过。

## 编排

1. 读取 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md`，取得公共输入、报告、结构化输出和批量结论规则。按 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md` 的 Story Traceability 解析真实故事来源、US ID 与本轮必要场景，不要求先发布草稿。
2. 按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 读取并注入 `${CLAUDE_PLUGIN_ROOT}/agents/web-demo-accept.md` 全文，逐文件串行派发独立 accept subagent。传入目标、feature/设计、故事映射、dev/test 原始证据入口、验证责任表和上游待验证场景；只加载当前文件相关上下文。
3. 由 agent 按领域 guide 核查真实类型检查入口、整文件运行与质量门禁，复用有效证据，仅补缺失/失效验证。入口不另抄命令或清单。
4. 按公共协议验证返回和报告；拒绝时记录责任与缺口，不修改源码或自动转入修复。中断时先确认旧 agent 已结束，核对已落盘结果再重派，避免重复运行。

批量模式对有效拒绝继续处理后续文件，并按公共协议写汇总报告、合并问题与待承接场景；派发失败或无效返回单独记为验收未完成，批次不能通过。单文件入口返回该 agent 的结构化结论和报告路径，不改写结论。
