---
name: t-prd-check
argument-hint: [feature-name|--all]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Bash
---

# PRD & User Story Quality Check

运行时边界统一参考：`protocols/runtime-boundaries.md`

## 目标
- 验证 PRD 文档完整性和规范性
- 评估用户故事质量（INVEST 原则、GWT 格式）
- 检查 PRD 与用户故事的一致性
- 检查 PRD / 用户故事是否错误混入接口、建表、schema 等实现细节
- 输出量化评分和修复清单

评分、扣分和问题分级统一参考：`protocols/prd-check-rubric.md`

## 使用方式
```bash
/t-prd-check [feature-name]
/t-prd-check --all
```

## 输入范围
- PRD 文档: `docs/prd/**/*.md`（排除 `00-index.md`）
- 用户故事: `docs/user-stories/**/*.md`
- 排除文件: `00-index.md`, `_roles.md`, `_README.md`, `client-app-settings.md`, `builtin_protection.md`

## 执行流程

### 1. 确定检查范围
- 解析命令参数，确定单功能或全量检查
- 使用 `Glob` 发现目标文件并排除特殊文件

### 2. 读取角色定义
- 读取 `docs/user-stories/_roles.md`
- 解析角色名称和技术标识，用于校验故事中的角色引用

### 3. PRD 检查
按 `protocols/prd-check-rubric.md` 执行：

- 基础章节检查
- 用户故事引用检查
- PRD 分层与禁止内容检查

### 4. 用户故事检查
按 `protocols/prd-check-rubric.md` 执行：

- 故事结构检查
- INVEST 原则检查
- 禁止内容检测
- 新文档质量门禁检查

### 5. 一致性检查
- 检查 PRD 中的用户故事链接是否有效
- 比较 PRD 与用户故事中的优先级是否一致
- 校验用户故事中的角色是否存在于 `_roles.md`

### 6. 评分计算
按 `protocols/prd-check-rubric.md` 计算：

- `PRD Score`
- `User Story Score`
- `Consistency Score`
- `Total Score`

### 7. 问题分级
问题分级统一参考：`protocols/prd-check-rubric.md`

### 8. 输出要求
- 控制台摘要和报告结构统一参考：`protocols/prd-check-rubric.md`
- 详细报告文件：`.ai/quality/prd-check-[YYYYMMDD-HHMMSS].md`

### 9. 失败处理
- 未找到文档：提示检查功能名称或改用 `--all`
- 文件解析错误：记录错误并继续其他文件
- 报告目录不存在：使用 `Bash` 创建 `.ai/quality/`

### 10. 相关引用
- `protocols/runtime-boundaries.md`
- `protocols/prd-check-rubric.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/product/index.md` - product guide 入口
- `${CLAUDE_PLUGIN_ROOT}/guides/product/user-story.md` - 用户故事规范和 INVEST 原则
- `${CLAUDE_PLUGIN_ROOT}/guides/product/prd.md` - PRD 分层与禁止内容规范
- `docs/user-stories/_roles.md` - 角色定义
- `skills/t-consistency-check/SKILL.md` - PRD 与后端实现一致性检查入口
