# 美术资产转换管线 · Asset Pipeline

> 现行美术规范见 [01-Architecture.md](../../docs/01-Architecture.md) 第四节；逐资产署名见 [assets/attribution](../../assets/attribution/README.md)。
> 主调为出版级写实 2D：`tikz-chemlab` 编译输出物为唯一主资产；`@itkdm/open-lab-components` 仅作 UI / 缩略图（HTML fragment 库，非 React）；3D 只做分子 / 晶体 / 球棍（3Dmol.js）。

## 用途

把上游资产转为产品可用资产：

| 上游 | 许可 | 转换 / 用途 |
|---|---|---|
| `tikz-chemlab`（LaTeX/TikZ，13 个器材宏） | LPPL-1.3c | `.tex` → `lualatex` PDF → `pdftocairo -svg` → `svgo` → 分层 SVG（**只转译编译输出物**）；实验台写实主资产 |
| `@itkdm/open-lab-components`（210 组件 / 化学相关 35 个，HTML fragment 库） | MIT | 无需转换；CSS 变量注入或 Web Component 封装；仅用于图鉴 / 资料卡 / 器材列表缩略图，不进写实主视图 |

**只转译编译产物、不 fork 源码**是不可绕过的第一原则（LPPL 1.3c Clause 1）。

## 转换链规范

统一使用 `lualatex → PDF → pdftocairo -svg → svgo`。DVI / dvisvgm 路径不可用（TikZ/PGF 在 DVI 模式注入 PostScript specials；dvisvgm 不支持 Ghostscript 10.02.1）。

产物为纯 `<path>`、零 `<text>` / 零外部字体，保留 `<g>` 分组与 `clipPath`（液位可控）。宏包源码与 TeX 中间产物只在构建期存在，不入库。

## 硬约束

1. **宏包源码不入库、不随产品分发**：`.sty/.tex/Obj.tex` 只在构建期存在；`.gitignore` 已排除构建目录与 TeX 中间产物（LPPL 1.3c Clause 1）。
2. **不修改宏包源码**：修改分发会触发 LPPL Clause 6（改名 + 变更日志 + 附完整原件），本管线不走该路径。
3. **每个 SVG 入库前**在 `assets/attribution/ASSETS.csv` 登记署名（含 pst-labo 四作者与「仅使用编译输出物」说明）。
4. **字体**：产物为纯路径、零 `<text>`，无需 woff 嵌入或转曲；若上游产出 `<text>`，须转曲后入库。
5. **动态化**：液位 / 颜色 / 倾斜用 `clipPath` + CSS 变量 + `transform`，不为每个状态生成一张 SVG。
6. **写实一致性**：`apparatus` 参数表是单一事实源，同时驱动 SVG 渲染、容器容量与物理约束；不混入卡通风格资产，`open-lab-components` 不进实验台主视图。
7. **跨平台**：转换须在 Windows（WSL2 / Docker Desktop）与 Linux 均可跑；路径小写、换行符 LF（见 `.gitattributes`），部署见 [deploy/README-windows.md](../../deploy/README-windows.md)。

## 新增一件器材的步骤

1. 确认上游来源：写实器材一律用 `tikz-chemlab` 宏；`open-lab-components` 仅用于 UI / 缩略图。
2. 生成 SVG，记录 `baselineY` / `mouthY` / 液位路径到 `apparatus` 参数表。
3. `ASSETS.csv` 增一行署名（含 pst-labo 四作者）；来自 open-lab-components 时 `used_in` 必须为 `ui/thumbnail`。
4. 跑 `schema-validate` + `asset-attribution` + 黄金用例。
5. 写实风格一致性人工复核（与出版级主调不符者退回）。
