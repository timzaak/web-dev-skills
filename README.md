# T-Tools — DDD 驱动的 Claude Code 开发工具集

一套面向 **Rust (Axum) + React** 项目的 Claude Code Plugin，覆盖从需求到验收的完整开发工作流。

## 一句话理解

> 把「写 PRD → 做技术设计 → 拆任务 → 写代码 → 跑测试 → 验收」这条链路，全部变成 Claude Code 的 `/` 命令，由专业 Sub-Agent 执行。

## 工作流全景

```
  /t-prd ──► /t-design ──► /t-task ──► /t-run ──► Finalize ──► Demo
    │            │             │          │            │           │
    ▼            ▼             ▼          ▼            ▼           ▼
 /t-prd-check /t-design-check /t-task-check   /t-backend-finalize /t-demo-run
                                                      │           │
                                                      ▼           ▼
                                              /t-consistency-check /t-demo-accept
```

每个节点都是一条 `/` 命令，背后对应一个 Skill + 一个或多个 Sub-Agent。

## 快速上手

### 安装

这是一个 **Claude Code plugin 源码仓库**。

- 插件内组件位于仓库根目录的 `skills/`、`agents/`、`protocols/`
- `.claude-plugin/plugin.json` 只是插件清单
- `spec/`、`docs/`、`.ai/` 指向的是 **目标项目运行时依赖**，不属于本插件仓库

使用前需要把本插件安装到 Claude Code 可识别的 plugin 目录，并根据目标项目结构校准命令和路径引用。

### 使用示例

```bash
# 1. 创建 PRD
/t-tools:t-prd create user-management

# 2. 生成技术设计
/t-tools:t-design user-management

# 3. 拆解任务
/t-tools:t-task user-management

# 4. 开始执行
/t-tools:t-run user-management --phase backend
```

## Skills 一览

### 主流程（按顺序执行）

| 命令 | 做什么 | 关键产出 |
|------|--------|----------|
| `/t-prd create [feature]` | 创建 PRD + 用户故事（GWT 格式） | PRD 文档 |
| `/t-design [feature]` | 生成技术设计（API / 数据库 / 前端 / 测试策略） | 设计文档 |
| `/t-task [feature]` | 按阶段拆解为可执行任务（phase → slot → item） | 任务清单 |
| `/t-run [feature] [--phase]` | 调度 Sub-Agent 逐项执行任务 | 代码实现 |
| `/t-backend-finalize [feature]` | 后端收口：clippy + fmt + 全量测试 + 自动修复 | 干净代码 |

### 质量检查

| 命令 | 做什么 |
|------|--------|
| `/t-prd-check [feature]` | PRD 质量评分（100分制） |
| `/t-design-check [feature]` | 设计文档质量评分（100分制） |
| `/t-task-check [feature]` | 任务规划质量评分（100分制） |
| `/t-consistency-check [module]` | PRD 与后端实现的一致性比对 |

### Demo 测试

| 命令 | 做什么 |
|------|--------|
| `/t-demo-run [测试文件]` | 运行单个 Playwright E2E 测试，失败自动诊断修复 |
| `/t-demo-run-all` | 批量运行所有 Demo 测试 |
| `/t-demo-accept [target]` | Demo 测试验收 |

### 独立 Skill

| 命令 | 做什么 |
|------|--------|
| `t-backend-test-run` | 后端测试运行 + 自动修复闭环（关键词触发） |

## Sub-Agents

每个 Agent 有明确的职责边界和执行模式：

| Agent | 角色 | 模式 |
|-------|------|------|
| `backend-dev` | Rust 后端开发（六边形架构） | Implementation |
| `backend-test` | 后端场景测试（BDD/GWT） | Implementation |
| `backend-accept` | 后端验收 | Review（只读） |
| `backend-consistency` | PRD 与实现一致性检查 | Review（只读） |
| `frontend-dev` | React 前端开发 | Implementation |
| `frontend-test` | Vitest 组件测试 | Implementation |
| `frontend-accept` | 前端验收 | Review（只读） |
| `demo-dev` | Playwright E2E 测试开发 | Implementation |
| `demo-accept` | Demo 验收 | Review（只读） |
| `demo-diagnose` | 失败诊断 + 诊断报告 | Analysis（只读） |

> **Implementation** = 可修改代码 | **Review/Analysis** = 只读分析，给出报告

## 项目结构

```
├── .claude-plugin/plugin.json    # 插件清单
├── skills/                       # 13 个 Skill（含模板和示例）
│   ├── t-prd/                    #   PRD 创建
│   ├── t-design/                 #   技术设计
│   ├── t-task/                   #   任务拆解
│   ├── t-run/                    #   任务执行
│   ├── ...                       #   检查 / 测试 / 验收
├── agents/                       # 10 个 Sub-Agent 定义
├── scripts/                      # Python 自动化脚本
│   ├── lib/                      #   共享库（paths, cli, docker, net, proc...）
│   ├── backend-test.py           #   后端测试调度
│   ├── demo-test-runner.py       #   Demo 测试运行
│   └── ...                       #   环境管理 / 格式检查
├── protocols/                    # 协议定义（诊断报告格式等）
└── README.md
```

## 技术栈

- **后端**: Rust / Axum / SeaORM / 六边形架构
- **前端**: React / TanStack Router & Query / Tailwind / Radix UI
- **测试**: cargo nextest / Vitest / Playwright
- **方法**: DDD / 用户故事 (GWT) / 分阶段任务规划

## 注意事项

- **插件内引用**：只应引用插件根目录中的 `skills/`、`agents/`、`protocols/` 等文件
- **目标项目依赖**：`spec/`、`docs/`、`.ai/` 代表目标仓库中的运行时文档和产物，使用时必须由目标项目提供
- **不使用 Claude Code Hooks**：所有自动化通过 Skills 内 Shell 命令实现，保证 Windows 兼容性
- **路径解析**：`scripts/lib/paths.py` 从自身位置向上推导项目根目录
- **针对特定项目**：Skills 中的路径、命令、触发条件需要根据目标项目调整

## 引用约定

- **插件内资源**：统一使用插件根语义路径，例如 `skills/t-run/SKILL.md`、`agents/backend-dev.md`、`protocols/tests-to-run-contract.md`
- **目标项目资源**：统一使用目标项目根语义路径，例如 `spec/backend/development.md`、`docs/prd/billing/shopify-pay.md`、`.ai/design/user-management.md`
- **避免混用**：不要再用 `../../agents/...`、`../protocols/...` 这类路径去表达插件内共享资源；也不要用 `../../spec/...` 去表达目标项目依赖
