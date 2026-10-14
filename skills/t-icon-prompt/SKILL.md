---
name: t-icon-prompt
description: Turn a vague icon idea into a ready-to-paste generation prompt card through a short guided Q&A. Use when the user wants an app icon, logo mark, favicon, or marketing icon prompt for any image generator or an SVG-writing agent. Produces prompts only and never generates images. Not for in-app UI icon sets; point those to icon libraries such as iconify or lucide.
argument-hint: "[icon-name]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
---

# 图标提示词引导

通过少量问答把"想要一个图标"收敛成一份可直接粘贴到任意图像生成工具（或交给 agent 写 SVG）的提示词卡。只产出提示词，不生成图片、不做图标集、不修改目标项目其他文件。用户要的是成套 UI 功能小图标时，引导改用 iconify / lucide 等图标库，不走本 skill。

## 输出

- `.ai/icon-prompt/<name>.md`，按 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-icon-prompt/template.md) 生成
- 产物正文用中文；prompt 本身用英文（生成模型对英文响应最好）

## 参数

- `$ARGUMENTS` 必须是图标名称；允许中文、英文、数字、空格、下划线、连字符
- 缺失或非法时终止并提示用法：`t-icon-prompt <name>`
- `.ai/icon-prompt/<name>.md` 已存在时走 update 路径：以旧卡为基底，只问变更项；用户在调用时已指明要改的维度的，跳过"要改哪些维度"确认，直接按问答脊柱问该维度。未变更维度原样保留旧卡结论与来源标签；变更维度按新回答重新标注来源，并重拼主 prompt 与备选方向、刷新生成时间。用户明确要求时才整卡重开

## 先查后问（Discover first）

先从目标项目查明背景信息，用于构造选项和推荐项；六个维度是判断或偏好，推断结果不能替代用户确认：

- 产品名、一句话价值：`README.md` 开头、`package.json` 的 name / description
- 产品类别：README、package.json keywords、目录结构（extension / miniapp / flutter / web）
- 品牌色：tailwind 配置、theme 目录、CSS 变量等品牌色定义文件

只有当前对话或用户指令已直接给出某维度结论时才跳过该维度；查明的背景信息写入产物并标注来源。当前目录不是可推断的项目（空目录、用户明确说与项目无关）时正常继续，全部维度走问答。

## 问答脊柱

六个维度逐项收敛；用户已给结论的不重复问，也不为同一维度二次提问；推断结果只用于构造选项和推荐项，不能替代用户确认。

| # | 维度 | 问法 | 选项要点 |
|---|---|---|---|
| Q1 | 用途载体 | 判断题，单问 | App 上架图标 / favicon+PWA / logo mark / 营销图；决定画布、形状和复杂度上限 |
| Q2 | 图形隐喻方向 | 判断题，单问 | 字母标 / 具象物隐喻 / 抽象几何 / 吉祥物；具象物候选项按产品类别从隐喻透镜取 |
| Q3 | 视觉风格 | 偏好题，可与 Q4/Q5 合并一次调用 | 扁平极简 / 渐变现代 / 线性描边 / 立体质感 |
| Q4 | 配色 | 同上 | 仓库品牌色（若推断到）/ 单色+强调色 / 配色速配建议 |
| Q5 | 气质 | 同上 | 专业可信 / 亲切活泼 / 科技前卫 / 温和自然；映射到形状语言 |
| Q6 | 排除项 | 约束题，单问 | 默认负面清单（画面文字、杂乱背景等默认项），用户可增删（如显式排除火箭、齿轮等俗套元素） |

提问规则：

- 每题最多 4 个选项，按上下文从 [references/prompt-craft.md](${CLAUDE_PLUGIN_ROOT}/skills/t-icon-prompt/references/prompt-craft.md) 词表挑最相关的，其余由 Other 兜底
- 判断题一次一问：先用一句话说明该维度决定什么、选偏的代价，标出推荐项和理由
- 回答含糊（"好看""高级""有质感"）时追问一次，要求可判断的指向：具体风格词、参考产品或色值；仍含糊则采用推荐项并标注"默认(未确认)"
- 用户要求跳过 → 采用推荐默认值，同样标注"默认(未确认)"
- 构造 Q2 / Q4 选项前读取 references 的隐喻透镜和配色速配；撰写 prompt 前读取主 prompt 解剖、风格冲突规则和负面清单

## 降级

`AskUserQuestion` 在当前会话不可用（如 Codex）时，按问答脊柱逐题纯文本提问，然后停下等待回答；不得替用户默认作答后继续。

## 生成提示词卡

1. 主 prompt 按 references 的固定结构拼装，不自创结构；负面清单包含 Q6 确认项。
2. 自检：风格、隐喻、质感描述词两两无冲突（用风格词表冲突规则）；主 prompt 覆盖全部已确认维度。检出冲突且双方均来自用户输入时，复述冲突词对让用户二选一后再拼装（该确认不受"不为同一维度二次提问"限制）；一方为默认(未确认)时保留用户确认方，被放弃方写入备选方向。
3. 产出主 prompt + 2 个备选方向（不同隐喻或风格的简写版，供 A/B 试验）。
4. 按 template 写入 `.ai/icon-prompt/<name>.md`，父目录缺失时创建。

## 收尾

- 报告产物路径
- 显式区分三类维度：用户确认、推断（含来源）、默认(未确认)
- 附上 references 的工具适配一行注
- 下一步建议：把主 prompt 粘贴到任意生成工具试 2–3 轮；想改哪个维度，重跑 `t-icon-prompt <name>` 走 update 路径

## 质量门禁

- 六个维度全部有结论，来源只允许 `用户确认`、`推断:<文件或对话>`、`默认(未确认)` 三种
- 主 prompt 覆盖全部已确认维度，无互相矛盾的描述词
- 产物落盘 `.ai/icon-prompt/`；不写 `docs/`，不生成图片，不改目标项目其他文件

## 失败处理

- 参数缺失或非法：终止并提示用法
- `.ai/icon-prompt/` 无法写入：终止并报告路径
- 问答中断：不持久化中间态；重跑时按"已存在 → update"路径从旧卡恢复
