# Demo 失败诊断报告协议

## 输出路径

- 目录：`.ai/diagnose/`
- 文件名：`[测试文件简名]-[YYYY-MM-DD-HH-mm].md`

## 固定元字段

每份报告都必须在开头给出以下字段：

- `runtime`: `web | flutter`
- `problem_code`: `TEST | FRONTEND | FLUTTER | NATIVE | BACKEND | ENV | AUTH | DATA`
- `severity`: `P0 | P1 | P2`
- `recommended_agent`: `web-demo-dev | flutter-demo-dev | frontend-dev | flutter-dev | backend-dev | manual`
- `confidence`: `high | medium | low`

字段含义：
- `problem_code`: 当前失败的唯一主分类
- `runtime`: 决定 TEST/DATA 应返回对应的 Web 或 Flutter Demo agent
- `severity`: 对当前修复优先级的判断
- `recommended_agent`: 推荐处理方；`manual` 表示需要人工处理环境或基础设施问题
- `confidence`: 对当前诊断结论的把握程度

## 标题规则

报告标题和章节标题必须携带具体结论，不得只写空泛容器名。

报告标题格式：

```md
# [problem_code/Px] [失败用例或测试文件] - [一句话根因]
```

章节标题使用固定顺序，但标题中必须填入本次诊断的关键信息：

- `失败事实: [动作/页面/接口] -> [错误表现]`
- `归因结论: [problem_code] -> [recommended_agent]`
- `证据链: [最强证据文件或请求]`
- `修复入口: [最小修改点]`
- `影响文件: [测试/证据/候选修复文件数量或核心文件]`
- `API复现: [method path status/error]`，可选
- `验证闭环: [最小重跑命令目的]`

说明：
- 第 6 节只在存在相关 API 失败证据时输出
- 其余 6 节为必填
- `[]` 中必须替换为真实内容，不得保留占位符
- 标题不要求长；如果标题无法写出具体内容，说明证据不足，应降低 `confidence`

## 各章节要求

### 1. 失败事实

至少包含：
- 错误信息
- 发生位置
- 测试文件 / 测试用例
- 一段最关键日志

如存在直接相关请求，可附一条失败请求摘要。

### 2. 归因结论

必须明确写出：
- `problem_code`
- `severity`
- `recommended_agent`
- `confidence`

只能有一个主分类。

### 3. 证据链

必须说明：
- 直接原因
- 间接原因
- 证据来源

证据优先级：
- 当前 runtime 的 `playwright-output.log` 或 `patrol-output.log`
- unified logs
- 测试代码 / 前端代码 / 后端日志

### 4. 修复入口

只保留对修复者真正有用的内容：
- 推荐修复方向
- 最小修改点
- 如有多个方案，最多列 2 个，且给出推荐方案

不要输出“成功率”“预计耗时”之类无可靠依据字段。

### 5. 影响文件

至少列出：
- 失败测试文件
- 主要证据文件
- 需要修改的候选文件

每项尽量带行号。

### 6. API复现

仅在问题与 API 请求直接相关时出现。

每条复现信息至少包含：
- `requestId` 或 `N/A`
- `status/error`
- `original_url`
- `normalized_url`
- 一条可执行 curl 命令

### 7. 验证闭环

必须给出最小回归命令，优先使用仓库统一入口。

至少包含：
- 当前失败用例或测试文件的最小重跑命令
- 若为环境相关问题，可补充健康检查命令

## 问题类型定义

| problem_code | 说明 | 推荐处理方 |
|---|---|---|
| `TEST` | 测试代码、选择器、断言、等待、流程问题 | web: `web-demo-dev`; flutter: `flutter-demo-dev` |
| `DATA` | 测试数据、前置条件、唯一性或初始化问题 | web: `web-demo-dev`; flutter: `flutter-demo-dev` |
| `FRONTEND` | 前端渲染、交互、路由、可见性、遮挡问题 | `frontend-dev` |
| `FLUTTER` | Flutter 页面、路由、状态或业务交互实现问题 | `flutter-dev` |
| `NATIVE` | Android 平台能力、权限或系统 UI 实现问题 | `flutter-dev` |
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

- `${CLAUDE_PLUGIN_ROOT}/agents/web-demo-diagnose.md` 与 `${CLAUDE_PLUGIN_ROOT}/agents/flutter-demo-diagnose.md` 必须引用本协议
- `${CLAUDE_PLUGIN_ROOT}/guides/web-demo/diagnose-guide.md` 只描述流程、证据优先级和产出时机
- `${CLAUDE_PLUGIN_ROOT}/guides/web-demo/templates/diagnose-report-template.md` 只是便捷骨架，不得与本协议冲突
