# [方案名称] Flutter 技术设计

**生成时间**: [自动生成时间戳]
**状态**: Draft
**主文档**: `.ai/design/[feature].md`

> 本文档是 Flutter 分端设计，以用户体验流为主，分层、状态与页面结构只做承载体验所需的最小技术映射；目标、范围与跨端决策以主文档为准。API 契约以后端分端设计为唯一来源，本文档只声明依赖。

## 1. 目标与范围（Flutter）

- 承接主文档目标的 Flutter 边界: [摘要]
- 不包含: [范围外项]

## 2. 需求来源与决策追踪

- 需求来源: [用户故事 / PRD / 技术预研路径引用，见主文档 §2]
- 关键 UX 期望: [入口、路径、反馈、默认值、错误状态]

| Decision ID | 状态 | 设计落点 | 说明 |
|---|---|---|---|
| `DEC-[feature]-001` | Applied / Not Applicable / Superseded | [章节] | [应用方式或不适用原因] |

## 3. 现有实现分析（Flutter）

> 只描述现状：现有分层、状态管理与路由方案、可复用点。

- `lib/...` - [现有页面/模块结构]
- 既定架构: [现有分层方式、Riverpod 使用现状、路由方案（如 go_router）]
- 可复用点: [已有 repository/service/widget]
- 受影响边界: [需要修改的模块]

## 4. 用户体验流

> 本节用用户视角语言描述，不展开技术实现；每个关键流程一段。

### 4.1 [流程名，如"绑定账号"]

- 入口: [用户从哪里进入这个流程]
- 操作路径: [用户每一步做什么]
- 系统反馈: [每步之后用户看到什么]
- 默认值: [表单/列表的默认选择与预填]
- 错误状态与恢复: [失败时用户看到什么、如何重试或纠正]

## 5. 架构与分层设计

- UI 层（view + view model）: [view 只负责渲染与转发用户事件；view model 负责取数、转换和 UI 状态]
- data 层（repository + service）: [repository 是数据单一来源（缓存、重试、错误处理）；service 无状态包装外部数据源]
- domain 层（可选）: [仅当多 repository 合并或逻辑被多个 view model 复用时引入；否则写"不引入"]
- 数据流向: [view ⇄ view model → repository → service → 外部数据源]

## 6. 状态管理设计（Riverpod）

- 状态管理方案: Riverpod 技术线，约束以 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/constitution.md` 为准；纯局部 UI 状态用 `StatefulWidget` + `setState`；不引入平行状态系统
- 状态划分: [哪些状态在 view model、哪些跨页面共享]
- notifier 划分: [按 feature/screen 划分的 `Notifier` / `AsyncNotifier` 及各自职责；异步数据用 `AsyncNotifier` 承载加载/数据/错误三态]
- 生命周期: [哪些 provider 需要 `autoDispose`、哪些保持全局]
- 不可变与事件分离: [状态对象不可变、事件与状态分离的落地方式]
- 订阅与重建范围: [消费端细粒度订阅（select），哪些 widget 会随状态重建、如何收敛范围]

### 6.1 API 依赖（只引用契约源）

- 契约源: `.ai/design/[feature]/backend.md` §4（或现有接口路径 `[METHOD] /api/...`）

| Operation ID | 方法 | 路径 | 使用的请求字段 | 使用的响应字段 | 用途 |
|---|---|---|---|---|---|
| [operationId] | [METHOD] | `/api/...` | [字段名列表] | [字段名列表] | [用途；不复制字段定义] |

## 7. 页面与导航设计（最小技术映射）

### 7.1 页面/组件清单

| 页面/Screen | 承载的体验流 | 用途 |
|---|---|---|
| `[screen or widget]` | [§4 中对应流程] | [用途] |

### 7.2 导航与路由

- 路由承接: [go_router 路由定义或变更；以项目现有路由方案为准]
- 页面关键状态: [加载、空态、错误、权限受限]

## 8. 平台与集成（如适用）

- [platform channel / 权限 / 生命周期 / 离线缓存；不涉及时写"不适用"及原因]

## 9. 依赖注入与可测试性

- 注入方式: [view model 对 repository 的依赖如何注入]
- 可测试边界: [哪些逻辑可脱离 widget 测试、mock 边界]

## 10. 性能考虑（仅当前必需）

- [rebuild 收敛 / const 构造 / 列表构建方式；无当前必需项时写"无"并说明]

## 11. Flutter 测试与 Demo 策略

- 单元/widget 测试: [测试入口与覆盖点；遵循 flutter 测试规范]
- Patrol Demo 主故事路径: [主故事验收路径；无需演示时明确说明]

## 12. 详细设计（Flutter 最小实现映射）

- 状态模型: [AsyncValue/不可变状态及加载、数据、空态、错误、提交中、权限受限转换]
- 关键事件与副作用: [Notifier 事件、repository 调用、导航或用户反馈]
- 公共边界: [新增或修改的 provider、repository/service 方法、路由；无则写“无”]

## 13. 风险与验证动作（Flutter 范围）

> 只记录方向已确定的风险和不需要用户选择的验证动作；需要用户裁决的问题必须已在主会话解决。

| 风险项 | 等级 (P0/P1/P2) | 缓解或验证动作 | 负责人 | 完成条件 |
|---|---|---|---|---|
| [风险描述] | [P0/P1/P2] | [动作] | [负责人] | [完成条件] |

## 14. 文件影响范围（Flutter 文件）

> 只列 Flutter 文件；全量汇总以主文档 §8 为准。MODIFY/DELETE 路径必须存在；CREATE 路径的父目录必须存在并说明命名依据。

| 文件 | 操作 | 说明 |
|---|---|---|
| `[真实仓库路径]` | CREATE / MODIFY / DELETE | [变更摘要] |
