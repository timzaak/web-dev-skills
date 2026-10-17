# 可选领域模板

模板由用户显式拉取、导出和选择。通用插件启动时不加载此目录中的角色、领域指南或应用脚本。

| 模板 | 内容 | 说明 |
| --- | --- | --- |
| [classic-stack](project-profiles/classic-stack/index.md) | 原 Rust/React、扩展、小程序、Flutter、Shopify 领域资产 | 保留 general 泛化时移除的角色、指南、脚本、测试与工程模板 |
| [java-backend](project-profiles/java-backend/index.md) | java 分支的 Java/Spring Boot/Maven 后端资产及适配 | 包含后端角色、开发/测试/验收实践、脚本与初始化模板 |

导出工具：`${CLAUDE_PLUGIN_ROOT}/scripts/export-template.py`。从本仓库根目录运行：

```powershell
python scripts/export-template.py list
python scripts/export-template.py export classic-stack --output C:/code/ai/t-tools-classic
python scripts/export-template.py export java-backend --output C:/code/ai/t-tools-java
```

输出目录须位于本仓库之外。脚本先在临时目录准备完整文件再交付；相同输出重复执行不重写，已修改或属于其他项目的非空目录拒绝覆盖。--dry-run 只检查与列出计划。

每份模板记录完整 upstream_revision 和 source_paths。files/ 中的领域源文件保持来源原文；通用支撑文件从该固定提交取出，不在此复制维护另一份结构协议。导出会生成完整、匹配该版本契约的独立插件，目录没有 .git，也不会复制当前未提交改动。

在目标项目中选择导出的插件：

```powershell
claude --plugin-dir C:/code/ai/t-tools-classic
# 或选择 Java 模板
claude --plugin-dir C:/code/ai/t-tools-java
```

这些运行时仍使用 t-tools 名称；同一会话只选择通用插件或一份导出模板。模板保留来源版本的命令/phase/state 行为，不能与 general 的 implementation 状态混用。需要通用主链路时，将已选实践整理到目标项目文档并使用通用角色；项目级专用角色注册仍按后续方案实现。

本地 Git 历史缺少固定提交时脚本停止，按对应模板的 upstream_branch 执行 git fetch origin main 或 git fetch origin java 后重试。导出不访问网络，不直接修改目标业务项目；应用环境和工程参数由模板初始化流程结合项目适配。

通用链接检查只检查此目录的说明和导航；files/ 中的 `${CLAUDE_PLUGIN_ROOT}` 指向导出后的独立插件根。必须导出后运行当前仓库的 check-markdown-links.py --root <导出目录>，并按模板相关脚本验证。维护与持续合并见[合并 main 指南](/human/merge-main.md)。
