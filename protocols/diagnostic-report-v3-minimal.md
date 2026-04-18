# 诊断报告协议 v3.0 - 极简版

## 目的

定义 `demo-diagnose` 输出给后续修复流程使用的最小诊断报告契约。

设计原则：
- 只保留修复和复现真正需要的信息
- 章节顺序固定，避免下游消费方猜测结构
- 使用 Markdown 文档，不要求 JSON
- 同时支持单用例失败和整文件失败
- API 复现信息为条件章节，仅在 API 类失败时出现

本文件是诊断报告结构的唯一真源。`agents/demo-diagnose.md` 只声明何时产出报告，`guides/demo/diagnose-guide.md` 只描述诊断流程；两者不得重新定义另一套字段或章节。

## 输出路径

- 目录：`.ai/diagnose/`
- 文件名：`[测试文件简名]-[YYYY-MM-DD-HH-mm].md`

## 固定元字段

每份报告都必须在开头给出以下字段：

- `problem_code`: `TEST | FRONTEND | BACKEND | ENV | AUTH | DATA`
- `severity`: `P0 | P1 | P2`
- `recommended_agent`: `demo-dev | frontend-dev | backend-dev | manual`
- `confidence`: `high | medium | low`

字段含义：
- `problem_code`: 当前失败的唯一主分类
- `severity`: 对当前修复优先级的判断
- `recommended_agent`: 推荐处理方；`manual` 表示需要人工处理环境或基础设施问题
- `confidence`: 对当前诊断结论的把握程度

## 报告结构

报告使用固定章节顺序：

1. `失败上下文`
2. `问题分类`
3. `根本原因分析`
4. `修复建议`
5. `相关文件`
6. `API复现命令（来自 network.json）`，可选
7. `快速验证命令`

说明：
- 第 6 节只在存在相关 API 失败证据时输出
- 其余 6 节为必填

## 各章节要求

### 1. 失败上下文

至少包含：
- 错误信息
- 发生位置
- 测试文件 / 测试用例
- 一段最关键日志

如存在直接相关请求，可附一条失败请求摘要。

### 2. 问题分类

必须明确写出：
- `problem_code`
- `severity`
- `recommended_agent`
- `confidence`

只能有一个主分类。

### 3. 根本原因分析

必须说明：
- 直接原因
- 间接原因
- 证据来源

证据优先级：
1. `playwright-output.log`
2. unified logs
3. 测试代码 / 前端代码 / 后端日志

### 4. 修复建议

只保留对修复者真正有用的内容：
- 推荐修复方向
- 最小修改点
- 如有多个方案，最多列 2 个，且给出推荐方案

不要输出“成功率”“预计耗时”之类无可靠依据字段。

### 5. 相关文件

至少列出：
- 失败测试文件
- 主要证据文件
- 需要修改的候选文件

每项尽量带行号。

### 6. API复现命令（来自 network.json）

仅在问题与 API 请求直接相关时出现。

每条复现信息至少包含：
- `requestId` 或 `N/A`
- `status/error`
- `original_url`
- `normalized_url`
- 一条可执行 curl 命令

### 7. 快速验证命令

必须给出最小回归命令，优先使用仓库统一入口。

至少包含：
- 当前失败用例或测试文件的最小重跑命令
- 若为环境相关问题，可补充健康检查命令

## 问题类型定义

| problem_code | 说明 | 推荐处理方 |
|---|---|---|
| `TEST` | 测试代码、选择器、断言、等待、流程问题 | `demo-dev` |
| `DATA` | 测试数据、前置条件、唯一性或初始化问题 | `demo-dev` |
| `FRONTEND` | 前端渲染、交互、路由、可见性、遮挡问题 | `frontend-dev` |
| `BACKEND` | 后端接口、查询、服务端异常 | `backend-dev` |
| `AUTH` | 登录、鉴权、授权、权限配置问题 | `backend-dev` |
| `ENV` | 环境启动、端口、依赖服务、基础设施问题 | `manual` |

## 严重级别定义

| 级别 | 说明 |
|---|---|
| `P0` | 当前测试无法继续执行或核心功能被阻塞 |
| `P1` | 功能路径受影响，需要尽快修复 |
| `P2` | 存在质量问题或次要缺陷，可延后处理 |

## 一致性要求

- `agents/demo-diagnose.md` 必须引用本协议
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/diagnose-guide.md` 只描述流程、证据优先级和产出时机
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/templates/diagnose-report-template-v3-minimal.md` 只是便捷骨架，不得与本协议冲突
