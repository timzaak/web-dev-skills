---
name: t-tech-research
context: fork
argument-hint: [feature-name]
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
  - Bash
  - WebSearch
  - Task
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
---

# 需求技术预研

运行时边界统一参考：`protocols/runtime-boundaries.md`

## 适用范围

这是一个有副作用的任务型 skill：会扫描代码库、搜索外部文档并写入预研报告。

仅在以下场景使用：
- 用户明确执行 `/t-tech-research [feature-name]`
- 用户明确要求对某项需求做技术可行性评估
- 需求涉及新依赖库、新技术栈、重大架构调整，需要先评估再进入 PRD 流程

不要因为用户只是问"这个库怎么用"或"大概怎么做"就自动触发本 skill。

默认不用于以下场景：
- 纯 bug 修复或小范围重构（无新依赖引入）
- 已有充分技术经验的标准实现
- 仅涉及内部代码重组

## 目标

基于用户的原始需求描述，扫描现有代码库，评估新依赖需求、研究最佳实践、分析对现有代码的影响，输出一份可行性判定报告供后续 `/t-prd` 参考。

输出文件：
- `.ai/tech-research/$ARGUMENTS.md`

如果未传 feature 名称，立即终止并提示：
`请提供 feature 名称。例如：/t-tech-research user-management`

## Input Contract

本 skill 处于 PRD 之前，无上游文档输入。输入为：
- 用户原始需求描述（通过参数或 `AskUserQuestion` 获取）
- 现有代码库（实时扫描）

可选输入（如果存在会提升质量）：
- `docs/prd/00-index.md` — 已有 PRD 索引（查找相关先例）
- `docs/user-stories/00-index.md` — 已有用户故事索引
- `.ai/design/**/*.md` — 已有设计文档（查找相关先例）

如果上游输入缺失，skill 仍可运行，但会在报告中标记缺失项。

## Output Contract

下游产出（供 `/t-prd` 参考和 `/t-design` 使用）：
- `.ai/tech-research/$ARGUMENTS.md` — 技术预研报告，包含：
  - 需求理解与技术需求提取
  - 现有代码库评估（依赖 + 可复用模块）
  - 差距分析
  - 库调研与最佳实践（如适用）
  - 影响分析
  - 可行性判定
  - PRD 编写建议
  - 参考资料

## 核心约束

- 依赖评估基于真实 `Cargo.toml` 和 `package.json`，不假设已有任何库
- 外部搜索（Context7 优先 → WebSearch 补充）仅用于库调研，不替代代码分析
- 影响分析中的文件路径必须使用仓库真实路径，不允许使用假设路径
- 先分析现有代码，再评估缺口；不凭空列举库
- 不产出 API 接口设计、数据库设计或任务拆解（那是 `/t-design` 和 `/t-task` 的职责）
- 保持 repo-agnostic，不硬编码特定业务路径或模块名
- 预研报告聚焦于"能否做""需要什么""影响什么"，不替代设计文档

## Claude Code 参数、提问与写文件规则

- `$ARGUMENTS` 是 Claude Code 传入的 feature 名称；它只用于确定输出文件名，不等于完整需求描述
- 如果用户已在当前对话中给出足够需求背景，不要重复使用 `AskUserQuestion`
- 只有在需求目标、约束、技术偏好或排除项不足以支撑可行性判断时，才补问最少问题
- 工具顺序必须遵循：先读依赖文件和已有文档，再扫代码，最后才用 Context7 或 `WebSearch`
- 写文件前先确认目标路径是 `.ai/tech-research/$ARGUMENTS.md`；若 `.ai/tech-research/` 不存在可创建，但若目标文件已存在，默认先询问是否覆盖
- 外部资料仅能补充库级事实、最佳实践和兼容性信息，不能覆盖本地代码扫描结论

## 先读这些文件

按以下顺序建立上下文（跳过不存在的文件）：
1. `backend/Cargo.toml` — 后端依赖清单
2. `frontend/package.json` — 前端依赖清单
3. `docs/prd/00-index.md` — 已有 PRD 索引
4. `docs/user-stories/00-index.md` — 已有用户故事索引
5. `.ai/design/**/*.md` — 已有相关设计文档
6. `${CLAUDE_PLUGIN_ROOT}/guides/backend/development.md` — 后端开发规范（如存在）
7. `${CLAUDE_PLUGIN_ROOT}/guides/frontend/development.md` — 前端开发规范（如存在）

## 工作流程

### 1. 验证参数

- 校验 `$ARGUMENTS` 非空
- 文件名仅允许中文、英文、数字、空格、下划线、连字符
- 拒绝 `..`, `/`, `\`
- 长度限制 1 到 50 字符

如果 `.ai/tech-research/$ARGUMENTS.md` 已存在，先询问是否覆盖。

### 2. 收集/明确需求

如果 `$ARGUMENTS` 仅是 feature 名称（没有详细描述），使用 `AskUserQuestion` 补齐以下内容：
1. 需求目标或问题陈述
2. 期望的技术能力或效果
3. 是否有特定的库或技术方向偏好
4. 是否有已知的约束或排除项

如果用户已经在当前对话中给出足够详细的需求描述，不要重复提问。

### 3. 扫描现有代码库

执行顺序固定如下：
1. 先读取依赖文件、索引和已有设计/PRD，建立本地上下文
2. 再扫描代码目录与可复用模块，确认真实实现入口和影响范围
3. 仅当本地分析表明需要新增依赖或补充库级事实时，才进行 Context7 / WebSearch

#### 3.1 盘点依赖

读取并分析（跳过不存在的文件）：
- `backend/Cargo.toml`（包括 workspace 成员和各 crate 的依赖）
- `frontend/package.json`（包括 dependencies 和 devDependencies）
- 相关 lock 文件中的版本信息（如 `Cargo.lock`、`package-lock.json`）

输出：
- 后端已有依赖清单（分 crate 列出直接依赖）
- 前端已有依赖清单（分 dependencies / devDependencies）
- 关键依赖版本和用途摘要

#### 3.2 识别可复用模块

扫描代码结构（跳过不存在的目录）：
- `backend/api/`
- `backend/core/`
- `backend/sdk/`
- `frontend/src/`

重点关注：
- 与需求相关的已有实现入口
- 可复用的工具函数、服务、中间件
- 现有架构模式和约定

如果代码分析较复杂，使用 `Task` 启动 Explore agent，给出清晰任务：
- 找出与需求相关的现有实现位置
- 标出可复用点
- 标出最可能受影响的模块
- 返回具体文件路径和理由

#### 3.3 查找相关已有文档

搜索：
- `docs/prd/**/*.md` — 相关已有 PRD
- `.ai/design/**/*.md` — 相关已有设计文档

提取相关文档中的关键决策和约束，避免重复研究。

### 4. 差距分析

对比需求与技术现状：
- 标记现有栈已覆盖的能力
- 标记需要新增或升级的依赖
- 标记可能需要替换的依赖
- 标记版本兼容性问题
- 标记现有代码需要修改以适配新需求的部分

### 5. 库调研（仅在需要新依赖时）

对每个需要引入的新库执行：

#### 5.1 解析库信息
- 使用 `mcp__context7__resolve-library-id` 解析库 ID
- 使用 `mcp__context7__query-docs` 查询：
  - 核心用法和 API 概览
  - 与本项目技术栈的集成模式
  - 版本迁移注意事项（如适用）
  - 常见陷阱和限制

#### 5.2 补充搜索（如 Context7 信息不足）
- 使用 `WebSearch` 搜索：
  - 官方文档和推荐用法
  - 与本项目技术栈的集成案例
  - 已知问题和社区反馈

#### 5.3 形成集成指导
对每个库输出：
- 库的基本定位和适用场景
- 推荐版本和引入方式
- 与本项目的集成步骤（最小可运行示例方向）
- 需要注意的配置、中间件注册或初始化逻辑
- 与现有库的交互（是否有冲突或协同）

如果不需要引入新依赖，跳过此步，在报告中写"现有依赖栈可满足需求"并说明理由。

### 6. 影响分析

扫描代码库，输出影响清单：

#### 6.1 文件级影响
- 需要新增的文件
- 需要修改的文件（按模块/目录分组）
- 可能受影响的配置文件
- 需要更新的测试文件

#### 6.2 架构级影响
- 需要调整的模块边界
- 需要变更的接口契约
- 需要调整的数据流或状态管理
- 中间件、拦截器或全局配置的变更

#### 6.3 风险矩阵

| 风险项 | 等级 | 影响范围 | 缓解措施 |
|---|---|---|---|
| [风险描述] | P0/P1/P2 | [影响范围] | [建议措施] |

### 7. 生成预研报告

使用 [template.md](template.md) 作为结构模板生成 `.ai/tech-research/$ARGUMENTS.md`。

如果某章节不适用，保留章节并标记"不适用"及原因，不要直接删掉导致结构不稳定。

### 8. 收尾输出

完成后在响应中明确说明：
- 报告路径
- 可行性结论（可行 / 有条件可行 / 需更多信息 / 不建议）
- 需要引入的新库数量和名称（如适用）
- 主要影响范围摘要
- 关键风险点
- 下一步命令：`/t-prd $ARGUMENTS`

## 质量门禁

生成前逐项自检：
- 是否基于仓库真实依赖文件做盘点（不是假设）
- 是否优先从现有依赖和代码中寻找解决方案
- 外部库调研是否覆盖了核心 API、集成方式和已知限制
- 影响分析中的文件路径是否使用仓库真实路径
- 可行性判定是否明确（不是模糊结论）
- 风险评估是否区分了 P0/P1/P2
- 是否避免替代设计文档的职责（不产出 API 设计、数据库设计、任务拆解）
- 是否把缺失信息写成显式假设

## 失败处理

- 参数缺失：终止并给出 `/t-tech-research [feature-name]` 示例
- 文件名非法：终止并说明允许字符范围
- 无法创建输出目录或写文件：终止并报告
- 需求描述不足：先补问；仍不足则继续，但在报告中写出缺口
- 既无代码库也无依赖文件：继续，但标记"无法评估现有实现，仅基于需求分析"
- Context7 查询无结果：降级到 WebSearch，在报告中标注信息来源
- WebSearch 也无结果：在报告中标记"外部信息不可用，依赖本地分析"

## 附加资源

- 预研报告结构模板：[template.md](template.md)

## 相关引用
- `skills/t-prd/SKILL.md`
- `skills/t-design/SKILL.md`
- `protocols/runtime-boundaries.md`
