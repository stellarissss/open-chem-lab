# 美术资产转换管线 · Asset Pipeline

> 现行美术规范见 [01-Architecture.md](../../docs/01-Architecture.md) 第四节。
> **状态**：转换链已实测——原 `DVI → dvisvgm` 与 `dvisvgm --pdf` 双路径均失败，唯一可行路径为 **`lualatex → PDF → pdftocairo -svg → svgo`**（实测证据见下文）。脚本骨架在 M1 落地为可批量运行版本；本目录当前为流程说明 + 示意脚本。
> **主调**：出版级写实 2D。tikz-chemlab 编译输出物为**唯一主资产**；`@itkdm/open-lab-components` **仅作 UI / 缩略图**（HTML fragment 库非 React）；**3D 只做分子 / 晶体 / 球棍模型**（3Dmol.js），程序化 3D 器材已降级为可选长线、不进 M1。

## 目的

把上游资产转成产品可用的资产：

| 上游 | 许可 | 转换 / 用途 |
|---|---|---|
| `tikz-chemlab`（LaTeX/TikZ，13 个器材宏） | LPPL-1.3c | `.tex` → **lualatex PDF → `pdftocairo -svg` → `svgo`** → 分层 SVG（**只转译编译输出物**）；实验台写实主资产 |
| `@itkdm/open-lab-components`（210 组件 / 化学相关 35 个，**HTML fragment 库**） | MIT | 无需转换；CSS 变量注入或 Web Component 封装；**仅用于图鉴 / 资料卡 / 器材列表缩略图，不进写实主视图** |

> **只转译编译产物、不 fork 源码**：这是本管线不可绕过的第一原则（LPPL 1.3c Clause 1）。

## 目录（M1 落地为可批量运行版本）

```
tools/asset-pipeline/
├── Dockerfile            # texlive + poppler-utils (pdftocairo) + svgo
├── build-tikz.sh         # 遍历 13 个宏批量生成 SVG，含参数化变体（主资产）
├── optimize-svg.sh       # svgo 优化 + CSS 变量替换（不再做字体转曲：产物本就零 <text>）
├── check-attribution.py  # 校验每个入库资产都在 ASSETS.csv 有署名
└── README.md             # 本文件：如何重跑、如何新增器材
```

> 早期草案中的 `extract-profile.mjs`（从 SVG 采样轮廓 → `LatheGeometry` 3D 器材）**已随程序化 3D 器材降级为长线而移出主流程**；架构规定（`docs/01-Architecture.md` 第二节）3D 只做分子级，不再需要器材 GLB 轮廓。若将来重启该长线，先询问用户裁决。

## 关键流程与命令（实测可行链）

```bash
# 1. 构建镜像
docker build -t st-asset-pipeline tools/asset-pipeline/

# 2. 从 CTAN 拉取 tikz-chemlab 源码到构建期临时目录（不入库），生成器材 SVG
docker run --rm -v "$PWD/assets:/out" st-asset-pipeline bash build-tikz.sh
#    内部：lualatex → PDF → pdftocairo -svg → svgo
#    → 只把 SVG 写入 assets/labware/，宏包源码与 TeX 中间产物全部留在构建容器内

# 3. 校验署名（CI 也跑）
python3 tools/asset-pipeline/check-attribution.py
```

**实测结论**：

| 原命令 | 结果 |
|---|---|
| `lualatex --output-format=dvi` → `dvisvgm` | 退出码 254 / `PostScript error: undefined in pgfwOperand`（TikZ/PGF 在 DVI 模式注入 PostScript specials） |
| `dvisvgm --pdf`（Ghostscript 10.02.1） | 退出码 252 / `The installed Ghostscript version 10.02.1 isn't supported` |
| **`lualatex → PDF → pdftocairo -svg`（poppler）** | **通过**：纯 `<path>`、零 `<text>` / 零外部字体、21 个 `clipPath`、保留 `<g>` 分组、液位 `liquidLevel1` 可控 |

> **禁止回退**到以上两条失败路径；双平台脚本统一用 `pdftocairo -svg`。

## 硬约束（不可绕过）

1. **宏包源码不入库、不随产品分发**：`.sty/.tex/Obj.tex` 只在构建期存在；`.gitignore` 已排除 `tools/asset-pipeline/build/` 与 TeX 中间产物。依据 LPPL-1.3c Clause 1（运行 Work 不受限制）。
2. **若必须修改宏包源码**：按 LPPL Clause 6 改名 + 附变更日志 + 附完整未修改原件，且放独立 `upstream/` 目录，先询问用户裁决。
3. **每个 SVG 入库前**在 `assets/attribution/ASSETS.csv` 登记署名（含 pst-labo 四作者与「仅使用编译输出物」说明）。
4. **字体**：`pdftocairo -svg` 产物为纯路径、零 `<text>`，**无需** woff 嵌入或转曲；如未来上游产出 `<text>`，须转曲后方可入库。
5. **动态化**：液位 / 颜色 / 倾斜用 `clipPath` + CSS 变量 + `transform`，不为每个状态生成一张 SVG。
6. **写实一致性**：`apparatus` 参数表是单一事实源，同时驱动 SVG 渲染、容器容量与物理约束；**不得混入卡通风格资产，open-lab-components 不得进入实验台主视图**。
7. **跨平台**：脚本需同时在 **Windows（WSL2 / Docker Desktop）与 Linux** 可跑；路径统一小写、换行符 LF（见 `.gitattributes`）。Windows 侧为 M0 受限项，M1 前补验。

## 新增一件器材的步骤

1. 确认上游来源：**写实器材一律用 `tikz-chemlab` 宏**；`open-lab-components` 仅用于 UI / 缩略图，不作器材主视图来源。
2. 生成 / 挂载 SVG，记录 `baselineY` / `mouthY` / 液位路径到 `apparatus` 参数表。
3. `ASSETS.csv` 增一行署名（含 pst-labo 四作者）；若来自 open-lab-components，`used_in` 必须为 `ui/thumbnail`。
4. 跑 `schema-validate` + `asset-attribution` + 黄金用例。
5. 写实风格一致性人工复核（与出版级主调不符者退回）。

## 历史实测结论与待办

**已实测核实**：转换链保真度；液体层可拆性（21 个 clipPath + `liquidLevel1` 可控）；open-lab-components 组件形态与用途（非 React、仅 UI / 缩略图）；3Dmol.js 许可证与 DOI（BSD-3 / `10.1093/bioinformatics/btu829`）；tikz-chemlab LPPL-1.3c；**Kenney 包内 LICENSE → CC0 1.0**；**3Dmol.js 真实浏览器 WebGL 球棍渲染 → Xvfb + SwiftShader `hasGeometry=true`**。

**仍待办**：13 个宏全量批量生成与单文件体积（内容生产）；**Windows 实机** Docker 卷挂载与路径换行符一致性，按 [`deploy/README-windows.md`](../../deploy/README-windows.md) 在本机补跑并回填（静态规范核查已通过）。
