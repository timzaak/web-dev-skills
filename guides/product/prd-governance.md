# PRD 治理建议（`t-dream` 报告输出）

在 `t-dream` audit 中输出 PRD 治理建议时读取本指南。目标是让 `docs/prd/**` 成为当前权威需求源：合并重复文档、归档或删除过期迭代记录、更新索引和引用。本指南只用于形成报告中的治理建议；`t-dream` 不执行写入，建议结构以 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md` 的 PRD Governance Recommendations 为准。

## 治理原则

- 先读全局：先读取目标目录的所有 PRD、`docs/prd/00-index.md`、总览/领域模型、相关已发布用户故事、相关 draft 用户故事和明显相关实现事实。
- 合并按稳定能力命名。例如 document 可收敛为 lifecycle / ingestion / retrieval-and-citations；infrastructure 可收敛为 storage / model-providers / observability / auth。
- 权威 PRD 只写当前规则：用户价值、范围、业务规则、状态、API 用户可见约束、验收目标、参考资料。
- 删除或压缩过程性内容：技术迁移步骤、依赖升级过程、旧实现替换流水账、已落地的临时方案、代码文件清单、数据库建表细节。
- 旧文档默认建议归档并标注非权威；只有用户明确授权删除时，才建议删除。
- 代码现状只用于校验当前事实；产品规则仍以当前需求判断表达。
- 冲突规则按更具体、更新、已实现或已被索引标为权威的来源裁决，并在新 PRD 中只保留裁决后的规则。
- 保持链接可达：建议同步更新 `docs/prd/00-index.md`、总览、领域模型、相关 PRD 的参考和用户故事引用。
- 整理建议中先区分 `.ai/user-stories` 候选来源与 `docs/user-stories` 已发布基线；不得把 draft story 静默当成已发布事实。

## 建议流程

1. **盘点范围**
   - 列出目标目录下 PRD 文件、大小、标题和状态。
   - 用 grep 查找重复或过期信号：`row_index`、`indexed`、`仅支持 xlsx`、旧 provider 名、旧存储名、`当前`、`迁移`、`实现`、`替换`。
   - 区分当前权威规则、历史背景和纯过程记录。

2. **设计合并目标**
   - 为每个能力域定义 2-5 个稳定权威 PRD。
   - 每个旧 PRD 必须映射到一个新 PRD、确认归档或在用户明确授权下确认删除。
   - 保留边界清晰的独立安全/集成 PRD，例如 API Token、Widget。
   - 输出合并 / 归档 / 删除映射表；如存在待产品裁决的冲突，先列为决策项。

3. **拟定新权威 PRD 要点**
   - 每份新 PRD 使用紧凑结构：标题、状态、创建时间、优先级、权威范围；相关用户故事表（只列 ID、标题、影响说明）；范围界定（包含/不包含）；当前业务规则和状态；API/前端用户可见约束；验收目标；参考资料。
   - 正文以当前规则为主线；如需说明历史，仅保留一句旧术语的非权威状态。

4. **旧 PRD 处置建议**
   - 默认建议移动到 `docs/prd/archive/...`，并在文件顶部标注“不再作为权威需求源”。
   - 只有用户明确允许删除时，才建议删除被合并旧文档。
   - 无论删除还是归档，都建议清理正式索引中旧文件入口。

5. **引用修正清单**
   - `docs/prd/00-index.md` 只列正式权威 PRD；如保留 archive，单独列归档且标明非权威。
   - 列出 `01-product-overview.md`、`02-domain-model.md`、相关 chat/integration/core PRD 中需更新的引用，以及仍指向旧文件的参考资料（如 `api-token-auth.md`）。
   - 用 grep 确认旧文件名、旧路径和旧术语没有作为当前权威规则残留。

6. **验证清单（供执行后使用）**
   - 运行项目已有 Markdown 链接检查脚本，例如 `python scripts/check-markdown-links.py`。
   - 检查所有 `docs/prd/**/*.md` 都出现在 `docs/prd/00-index.md`，除非明确是 archive 且索引策略排除。
   - 运行 grep 确认旧 PRD 路径、删除文件和过期当前规则没有死引用。

## PRD 合并判定

建议合并：
- 多个 PRD 描述同一对象的不同迭代，例如 xlsx 导入、Markdown 上传和 page_id 统一都属于文档摄入。
- 文档大部分在讲“从旧实现迁移到新实现”，而当前代码已实现。
- 不同文档重复状态机、ID 语义、metadata 字段、provider 配置或存储边界。
- 旧文档标题是一次性方案名。

建议保留独立：
- 安全边界独立且影响多类 API，例如 API Token 鉴权。
- 对外集成契约独立，例如嵌入式 Widget。
- 用户可见体验明显独立，例如聊天 UI、多轮记忆。
- 尚未稳定的候选方案；它应放在 `.ai/future/**`，不作为正式 PRD。
