# Figma 资产落位

执行方法页。资产结构、命名和覆盖规则以 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md` 的 `Asset Processing` 与 `assets-manifest.json Structure` 为准。

## 1. 在 MCP 窗口内取得原始字节

调用 `get_design_context` 后，从返回内容中收集本次实现实际需要的图片、图标和 SVG URL。Figma 资产 URL 是临时引用，只能作为下载来源，不能直接写进正式代码。

按以下顺序处理：

1. 优先下载 design context 已返回的资产 URL。
2. 缺少所需资产或需要特定节点导出格式时，若 remote MCP 暴露 `download_assets`，调用后下载它返回的临时 URL。
3. 原始字节写入 `.ai/figma/<id>/raw/<name>.<ext>`，并在 `spec.json.assets` 记录 `{id, name, kind, source, rawPath}`。
4. 无法取得的资产立即报告并停止，不使用占位图、截图裁切、自绘 SVG 或新图标包代替。

`download_assets` 是 remote-only 可选能力，不要求桌面 MCP 提供。它不会直接写本地文件，也不提供原始视频。依赖视频的设计必须由人类给出项目资产或 CDN 来源。

## 2. 语义化命名

名称依次取：

1. 已经语义化的 Figma 图层名，例如 `Hero Background` → `hero-background`。
2. 节点角色与父级上下文，例如 `ProductCard` 内的默认名 `Vector` → `product-card-icon`。
3. 仍无法判断时请求人类命名。

沿用 context 声明的 `kebab-case` 或 `snake_case`。禁止节点 ID、数字序号、纯 hash 和 `Frame 12`、`Image`、`Vector` 等默认名。构建工具生成的 contenthash 不影响源文件命名。

## 3. 探测正式资产位置

按以下优先级确定目录、命名和引用方式：

1. 项目 `DESIGN.md` 中已有的目标 Web 约定。
2. 目标文件及邻近模块已有的 `import`、`<img src>`、CSS `url()` 或 CDN 用法。
3. 已识别框架的明确约定目录，例如 Next/Vite 的 `public/` 或项目既有 `src/assets/`。

只有多个位置都合理且无法从代码判断时才请求人类选择。没有资产时在 context 写「不适用」，不得因为项目尚无资产目录而阻塞。

## 4. 原样落位并防止覆盖

默认把 raw 原始字节复制到正式目录，不统一转 WebP、不重绘 SVG、不转码媒体。若项目 `DESIGN.md` 明确要求转换，按项目自己的工具和规范执行，不在本通用 guide 中硬编码格式或质量参数。

写入前处理同名文件：

- 目标不存在：写入并计算 SHA-256。
- 目标存在且 SHA-256 相同：直接复用。
- 目标存在但 SHA-256 不同：停止并请人类选择新名称或确认替换，禁止静默覆盖。

完成后写 `.ai/figma/<id>/assets-manifest.json`：

```json
[
  {
    "id": "1:5",
    "name": "hero-background",
    "kind": "image",
    "source": "design-context",
    "outputPath": "public/assets/hero-background.png",
    "sha256": "<64 lowercase hex chars>"
  }
]
```

无资产时写 `[]`。manifest 只包含成功落位的资产；失败项阻塞进入实现阶段。`raw/` 可在流程完成后手动清理。

## 5. 交付验收

还原 agent 只引用 manifest 的 `outputPath`。验收时逐项确认：

- `outputPath` 存在且位于项目内；
- 文件 SHA-256 与 manifest 一致；
- 页面没有对应资源加载失败；
- `baseline.png` 与 `actual.png` 中的资产内容由人类视觉复核，computed-style delta 只负责布局和样式收敛。
