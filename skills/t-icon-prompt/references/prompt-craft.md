# 图标提示词工艺

读取时机：构造 Q2 / Q4 选项前读"隐喻透镜"和"配色速配"；撰写 prompt 前读"主 prompt 解剖"、"风格词表"和"负面清单"。

## 主 prompt 解剖

固定结构，槽位顺序不调换，风格词紧跟主体：

```text
[icon type] of [metaphor/subject], [style descriptors], [color palette],
[shape/canvas], centered composition, [mood/shape language],
no text, no letters, clean edges, readable at small sizes
```

| 槽位 | 说明 | 示例 |
|---|---|---|
| icon type | 载体类型词 | `app icon` / `flat icon` / `logo mark` / `icon symbol` |
| metaphor/subject | 具体主体，一句话可想象 | `an origami fox curled into a circle` |
| style descriptors | 从风格词表取 2–3 个词 | `flat design, minimal, solid colors` |
| color palette | ≤3 色，写角色而非罗列色值 | `deep navy with a single cyan accent` |
| shape/canvas | 画布约束 | `rounded-square app icon, full-bleed` / `centered mark on plain white background` |
| mood/shape language | 气质映射 | `soft rounded corners and gentle curves` / `sharp geometric angles` |

填充示例：

```text
app icon of an origami fox curled into a circle, flat design, minimal,
solid colors, warm coral with amber accent, rounded-square app icon,
full-bleed, centered composition, soft rounded corners, no text,
no letters, clean edges, readable at small sizes
```

隐喻选字母标时：主体写 letterform（如 `a bold lowercase letter t formed by a merging arrow`），固定尾部的 `no text, no letters` 替换为 `single letterform only, no additional text`，负面清单同步去掉 `no letters`。

## 风格词表

| 风格 | 英文描述词 | 适用气质 | 冲突规则 |
|---|---|---|---|
| 扁平极简 | flat design, minimal, simple geometric shapes, solid colors | 全能默认 | 与 3D、渐变、描边类互斥 |
| 渐变现代 | modern gradient, duotone, smooth color transition | 科技、前卫 | 与扁平、描边互斥 |
| 线性描边 | monoline outline, consistent stroke weight | 工具、温和 | 笔画过细在小尺寸消失；与色块类互斥 |
| 立体质感 | 3D render, soft clay, glassmorphism | 活泼、前卫 | 细节在小尺寸丢失；与扁平、描边互斥 |
| 手绘 | hand-drawn, sketchy lines, imperfect strokes | 亲切 | 与几何类互斥 |
| 像素复古 | pixel art, 8-bit | 复古、社区 | 严肃产品慎用 |

自检规则：主 prompt 中任意两个风格/质感词命中同一冲突关系即矛盾，必须二选一后重拼。

## 隐喻透镜（按产品类别）

| 类别 | 候选具象物 |
|---|---|
| 效率/工具 | 折纸、快门、合并的箭头、收纳盒 |
| 开发/工程 | 代码括号、终端光标、分支图、积木 |
| AI/自动化 | 编织线、绳结、流形、星轨 |
| 金融/数据 | 上升折线、堆叠硬币、天平、量角器 |
| 社交/沟通 | 对话气泡、交汇的圆、回声波纹 |
| 内容/创作 | 书页、调色刀、音符、取景框 |
| 安全 | 盾牌、锁孔、堡垒轮廓 |
| 健康/生活 | 心形脉搏、叶子、水滴 |

俗套警示（可用但平庸，除非用户点名）：火箭=增长、齿轮=效率、灯泡=想法、放大镜=搜索、发光大脑=AI、握手=合作。构造选项时俗套元素不进入推荐项。类别不在表内时，Q2 只给四个方向选项，具象物候选留给用户通过 Other 表达。

## 配色速配

原则：≤3 色，一主一辅一强调；小尺寸下必须保留深浅两档对比。

| 气质 | 公式 | 示例 |
|---|---|---|
| 专业可信 | 深蓝主色 + 单一冷色强调 | navy + cyan |
| 科技前卫 | 深底 + 同色系渐变 | indigo→violet |
| 亲切活泼 | 双暖色明快组合 | coral + amber |
| 温和自然 | 低饱和自然色 | sage green + terracotta |

## 负面清单默认项

```text
no text, no letters, no watermark, no clutter, no busy background,
no multiple subjects, no thin details that vanish at small sizes
```

按风格增删：扁平、描边、渐变类追加 `no photorealism`；线性描边追加 `no fill`；立体质感追加 `no flat shading`；字母标去掉 `no letters`。

## 工具适配一行注

不改动 prompt 主体，只在交付时附带：

- Midjourney：末尾补 `--ar 1:1`（App 图标、logo mark）等比例参数
- Recraft 等矢量优先工具：保留 vector / SVG 导出意图，选对应风格 preset
- 交给 agent 写 SVG：不用自然语言 prompt，改写为 SVG spec（viewBox、色值、形状语言、图层数上限）
