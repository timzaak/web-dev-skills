# T-Tools 的结构

T-Tools 把工程工作流与项目领域分开：插件负责如何可靠推进，目标项目提供具体工程规则。

| 位置 | 职责 |
| --- | --- |
| skills/ | 阶段编排、前置校验、选择角色、状态推进、失败恢复与产物汇总 |
| agents/ | 单一角色执行或独立只读检查，不承担跨阶段编排 |
| protocols/ | 状态、输出、评分、调度与门禁的唯一共享契约 |
| guides/ | 通用工程实践，以及保留的 Web Demo / Figma 专用指南 |
| scripts/ | 可重复、必须确定执行的工具 |
| templates/project-profiles/ | 显式拉取的领域源模板，导出时使用固定版本的配套运行时 |
| human/ | 结构解释、使用说明与后续方案，不作为运行时状态源 |

## 主链路

立项后按主要未知项进入 PRD 或技术预研，在设计前收敛。纯技术且不改变产品语义的工作才可仅从预研进入设计。设计基于真实模块，使用通用 project-design 角色；implementation 的 project-dev/test/accept 分别实现、测试与只读验收，Web Demo 仍有独立角色。

默认 t-super-run 合并目标级计划与执行：主会话持续完成 dev/test，accept 独立派发。每次只执行显式 phase，落盘到 `.ai/super-run/<feature>/`，同一命令可恢复。需要独立计划审阅时使用 t-task -> t-run，按 phase/slot/item 串行执行，状态在 `.ai/task/<feature>/`。两套状态互不迁移。

## 真源与门禁

当前实现以目标项目代码和配置为准，工程约束来自 AGENTS.md 与已确认项目文档。插件共享结构在 [protocols/index.md](/protocols/index.md)，边界在 [runtime-boundaries.md](/protocols/runtime-boundaries.md)。项目命令必须真实存在，缺失或失败不能回退其它技术栈。

前置质量检查可选；实现后的独立 accept 必须有可复核证据。后续修改使证据失效时重新打开受影响工作及验收。质量收口遵循 review --fix -> simplify -> push，发布由 release 协议入口约束。

## 领域知识

插件不再内置生产领域 guides、专用实现角色或应用脚手架。项目内知识从实际实现和验证产生，新的偏好需要人选择，未确认不能升级为正式规则。详见 [泛化原则](/human/generalization.md) 与[后续方案](/human/generalization-plan.md)。

skill 交付适用 [skill 创作指南](/guides/core/skill-authoring.md) 与[行为验证指南](/guides/core/skill-testing.md)。Web Demo 与 Figma 按各自索引加载，不默认载入全部指南。
