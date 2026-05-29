---
name: t-tech-research
description: Research technical feasibility for a feature by scanning the codebase, checking dependencies, researching new libraries when needed, and writing a report under .ai/tech-research/. Use when the user runs /t-tech-research with a feature name, asks for a technical feasibility study, or requests evaluation before PRD work for a feature involving new dependencies, new technology, or significant architecture changes. Do not use for casual "how would this work" questions, ordinary bug fixes, or small refactors.
---

# 需求技术预研

## 目标

基于用户需求和现有代码库，评估技术可行性、依赖缺口、代码影响范围和关键风险，生成报告供后续 `/t-prd` 参考。

输出文件：
- `.ai/tech-research/$ARGUMENTS.md`

如果未传 feature 名称，立即终止并提示：
`请提供 feature 名称。例如：/t-tech-research user-management`

## 输入与输出

输入：
- 用户原始需求描述（参数、当前对话或补问获取）
- 现有代码库
- 可选：`docs/prd/00-index.md`、`docs/user-stories/00-index.md`、`.ai/design/**/*.md`

输出报告必须包含：
- 需求理解与技术需求提取
- 现有代码库评估（依赖和可复用模块）
- 差距分析
- 库调研与最佳实践（如适用）
- 影响分析
- 可行性判定
- PRD 编写建议
- 参考资料

## 参数规则

- `$ARGUMENTS` 只用于确定输出文件名，不等于完整需求描述
- 文件名仅允许中文、英文、数字、空格、下划线、连字符
- 拒绝 `..`, `/`, `\`
- 长度限制 1 到 50 字符
- 如果 `.ai/tech-research/$ARGUMENTS.md` 已存在，先询问是否覆盖

## 核心约束

- 先分析现有代码和依赖，再评估缺口；不凭空列举库
- 依赖评估必须基于真实 `Cargo.toml`、`package.json` 和 lock 文件（如存在）
- 外部搜索只用于库级事实、最佳实践和兼容性信息，不能替代本地代码分析
- Context7 优先，WebSearch 只作补充
- 影响分析中的文件路径必须使用仓库真实路径
- 不产出 API 接口设计、数据库设计或任务拆解
- 报告聚焦于"能否做""需要什么""影响什么"
- 讨论时可多方案；最终报告必须收敛为单一、明确、可执行的技术路线
- 最终报告不得保留方案对比、候选排序或"可选/视情况"等开放式描述
- 被排除方向只写成确定约束或风险，不展开对比
- 缺失信息必须写成显式假设

## 工作流程

### 1. 明确需求

如果当前对话中已有足够需求背景，不要重复提问。

仅在需求目标、约束、技术偏好或排除项不足以支撑可行性判断时，补问最少问题：
- 需求目标或问题陈述
- 期望的技术能力或效果
- 特定库或技术方向偏好
- 已知约束或排除项

补问后，无论用户是否全部回答，都必须在写报告前将未回答项转为显式假设并写入报告 6.2 节。不得在报告中留下"待确认"/"需确认"/"待定"/"TBD"等未决项。

### 2. 建立本地上下文

按需读取以下文件，跳过不存在的文件：
- `backend/Cargo.toml`
- `frontend/package.json`
- `Cargo.lock`
- `package-lock.json`
- `docs/prd/00-index.md`
- `docs/user-stories/00-index.md`
- `.ai/design/**/*.md`

扫描真实代码目录，重点关注：
- `backend/api/`
- `backend/core/`
- `backend/sdk/`
- `frontend/src/`

如果代码分析较复杂，可委托探索任务，要求返回相关实现位置、可复用点、影响模块和理由。

### 3. 分析差距

对比需求与现状，明确：
- 现有栈已覆盖的能力
- 需要新增或升级的依赖
- 可能需要替换的依赖
- 版本兼容性问题
- 现有代码需要修改的部分

### 4. 调研新依赖

仅当本地分析表明需要新依赖或需要补充库级事实时执行。

对每个候选库调研：
- 核心用法和 API 概览
- 与目标项目技术栈的集成方式
- 版本迁移注意事项（如适用）
- 常见陷阱、限制和兼容性问题
- 推荐版本和引入方式

如果不需要新依赖，在报告中写明"现有依赖栈可满足需求"并说明理由。

### 5. 决策收敛

把本地分析、依赖调研和人类讨论收敛为一个最终技术路线。

收敛规则：
- 只把最终选定的依赖、集成方式、影响范围和风险写入报告
- 不保留候选比较、备选路线或"可二选一"表达
- 无法收敛时，结论写"需要更多信息"，并列出阻塞问题
- 已排除方向只作为确定约束或风险写入

### 6. 生成影响分析

输出文件级和架构级影响：
- 需要新增或修改的文件
- 可能受影响的配置文件和测试文件
- 需要调整的模块边界、接口契约、数据流或全局配置
- 风险矩阵，风险等级使用 P0/P1/P2

### 7. 写入报告

使用 [template.md](template.md) 的结构生成 `.ai/tech-research/$ARGUMENTS.md`。

如果某章节不适用，保留章节并标记"不适用"及原因，不要直接删除。

## 收尾输出

完成后说明：
- 报告路径
- 可行性结论（可行 / 有条件可行 / 需更多信息 / 不建议）
- 需要引入的新库数量和名称（如适用）
- 主要影响范围
- 关键风险点
- 下一步命令：`/t-prd $ARGUMENTS`

## 质量门禁

生成前自检：
- 是否基于真实依赖文件做盘点
- 是否优先从现有依赖和代码中寻找方案
- 外部库调研是否覆盖核心 API、集成方式和已知限制
- 是否已收敛为单一明确技术路线
- 是否移除了方案对比、候选排序和开放式选择
- 报告是否不含任何"待确认"/"需确认"/"待定"/"TBD"等未决项；未确认信息是否已全部转为显式假设
- PRD 编写建议是否明确可执行
- 影响分析中的路径是否真实存在
- 可行性判定是否明确
- 风险评估是否区分 P0/P1/P2
- 是否避免替代 `/t-design` 和 `/t-task` 的职责

## 失败处理

- 参数缺失：终止并给出 `/t-tech-research [feature-name]` 示例
- 文件名非法：终止并说明允许字符范围
- 无法创建输出目录或写文件：终止并报告
- 需求描述不足：先补问；仍不足则继续，但在报告中写出缺口
- 既无代码库也无依赖文件：继续，但标记"无法评估现有实现，仅基于需求分析"
- Context7 查询无结果：降级到 WebSearch，在报告中标注信息来源
- WebSearch 也无结果：在报告中标记"外部信息不可用，依赖本地分析"
