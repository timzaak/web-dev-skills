# general 分支持续合并 main

本指南用于把 origin/main 的持续更新合入 general，同时保持通用工作流与可选领域模板的边界。它不授权自动提交、推送或覆盖用户改动；开始合并前读取本文件及仓库 AGENTS.md。

## 1. 三个需要维护的版本

- general 主目录：通用编排、状态、恢复与验收；Web Demo/Figma 保留。
- classic-stack 模板：从 main 迁移的生产领域内容，清单与来源见 templates/project-profiles/classic-stack/template.json。
- java-backend 模板：从 java 分支提取的 Java 后端和配套适配，清单与来源见 templates/project-profiles/java-backend/template.json。

模板 files/ 保存领域源文件；共享运行时从各自 upstream_revision 的 Git 历史取出。每份模板有独立兼容基线，main 合并成功不等于模板已升级。修改模板内容与推进 upstream_revision 应在同一轮验收，不把来源分支名当作浮动运行版本。

## 2. 合并前准备

在仓库根目录执行：

```powershell
git status --short
git branch --show-current
git fetch origin main
git log --oneline --left-right general...origin/main
git diff --name-status general...origin/main
```

必须在 general，且本轮改动已有独立提交或明确备份后才开始 merge。工作区有未提交内容时先整理，不执行 reset --hard、clean 或自动 stash 来替用户处理。记录合并前 HEAD 和两个模板的 upstream_revision，作为冲突判断与验证依据。

按本次 diff 读取变动的 skill 及其 protocol/guide/agent/script 和下游消费者。检查是否新增了此前没有的语言、平台、phase 或项目运行时目录。

## 3. 归属与合并策略

| main 的变化 | general 的处理 |
| --- | --- |
| 通用阶段编排、状态、恢复、输出、评分、调度 | 合入主目录的共享契约，检查全部消费者；保留领域解耦 |
| Web Demo、Figma、logger package | 合入保留能力，并检查是否夹带生产技术栈默认值 |
| 后端/前端/移动端/扩展等专用角色与指南 | 更新 classic-stack/files 中的同名来源路径，主目录继续移除 |
| Java 后端资源 | 通过 java 模板单独更新，不让它覆盖 classic-stack 的 Rust 资源 |
| 混合通用与领域内容的 skill/protocol/script | 按规则拆分：通用部分合主目录，领域部分由模板保留；不能整文件任选 ours/theirs |
| 新框架、新平台或新领域文件 | 先分类，再补充对应模板 source_paths；不能因为它是新增文件就默认注册到主链路 |
| README、安装说明、插件元数据 | 保持 general 公开入口正确，领域能力在模板目录宣传；不恢复默认 targetStack |
| 测试 | 主目录测试验证通用行为；领域测试迁入模板并在导出运行时执行，避免仅删除失败测试 |

## 4. 执行合并与处理冲突

```powershell
git merge origin/main
```

出现 modify/delete 冲突通常意味着 main 修改了已迁移的领域文件。先核对 main 版本、旧模板版本和本分支是否有独立修订，再把需要保留的内容合到模板同名路径，最后用 git rm -- <已确认迁移的原路径> 维持主目录删除状态。没有冲突的新领域文件也要执行分类迁移。

可用以下只读命令查看三方来源：

```powershell
git status --short
git diff --name-only --diff-filter=U
git show origin/main:agents/backend-dev.md
git show HEAD:templates/project-profiles/classic-stack/files/agents/backend-dev.md
```

尚未提交的首次模板文件以工作区为准，不强求 HEAD 已有该路径。模板与 upstream 均改动同一段时人工合并，保留模板的适配记录。禁止批量接受 ours/theirs 来消除整组协议冲突；旧 phase 枚举、九字段 change_scope、框架硬编码 CI/环境不应重新覆盖通用主目录。

需要放弃尚未完成的 merge 时，仅在确认没有合并开始后新增的用户工作后使用 git merge --abort；不能用强制重置代替恢复。

## 5. 更新领域模板的来源基线

先比较 template.json 中旧 upstream_revision 与拟采用的完整提交，核对 source_paths 的每个新增、修改和删除。使用 git diff <旧提交> <新提交> -- <来源路径列表>；同时查看未在清单内的新领域文件。

模板内容按文件从来源提交提取，文本和二进制都通过字节写入，避免 PowerShell 重定向改变编码。例如下面的命令只更新已审阅的一个来源文件：

```powershell
python -c "from pathlib import Path; import subprocess; p='agents/backend-dev.md'; dst=Path('templates/project-profiles/classic-stack/files')/p; dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(subprocess.check_output(['git','show','origin/main:'+p]))"
```

模板已有独立修改时先比较，不能直接执行覆盖。新来源增加文件则补 source_paths；来源删除文件时检查模板是否仍需要，移除后同步清单与导航。清单列出的文件必须在 files/ 实际存在。

选定新基线后，将 upstream_revision 更新为 git rev-parse origin/main 的完整提交。即使某些领域源文件未变化，也要验证新基线的共享协议、设计模板、执行入口和脚本依赖与它们兼容。不能仅修改这个字段就宣称模板升级完成。

Java 模板使用 git fetch origin java 和 origin/java 同样处理。它可以晚于 main 更新，保持原固定提交仍可导出；不需要为了合并 main 而 git merge origin/java。若希望把 Java 实现移植到更新的 main 基线，必须完整处理 Java 的脚本/协议适配并单独验证，不把两个版本的状态协议拼接。

## 6. 验证与收口

通用主目录：

```powershell
python -X utf8 -m unittest discover -s scripts/tests -v
python -X utf8 scripts/check-markdown-links.py
git diff --check
```

检查主目录未重新出现默认领域 guides、专用 agent、框架固定命令或不适用的 phase。对 changed skill 走读正常路径、缺输入、下游门禁、失败恢复与重复执行；check 仍可选，accept 不被替代。logger package 有改动时在 package 内运行对应 npm 脚本。

对每份本轮受影响模板，导出到仓库外的新临时目录：

```powershell
python scripts/export-template.py export classic-stack --output C:/temp/t-tools-classic-merge-check
python -X utf8 scripts/check-markdown-links.py --root C:/temp/t-tools-classic-merge-check
python -X utf8 -m unittest discover -s C:/temp/t-tools-classic-merge-check/scripts/tests -v
```

Java 模板替换为 java-backend 并使用另一个新目录。导出目录非空且已有改动时换新目录，不为通过验证而删除用户内容。模板固定提交缺失时先 fetch 对应分支；来源分支历史重写且无法取得提交时停止，恢复来源或明确升级基线，不能静默改取最新版。

链接检查报告必须核对死链接/不可达数量，脚本退出码本身不代表没有问题。模板原有的已知基线问题要记录来源、影响与后续处理；不能归咎于本次合并后直接忽略新失败。若本轮只改通用内容且模板来源/导出器均未变，不重复运行无关领域测试。

最后检查全部冲突已解决，README 中英文、模板说明、source_paths 和 upstream_revision 一致，且只包含本轮有意变更。报告通用改动、模板改动、基线迁移和验证结果，再按用户授权提交/推送。模板发布或知识方案实现需要各自授权，不由一次 merge 扩张范围。
