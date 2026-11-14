# 美术资产转换管线 · Asset Pipeline

> 设计见 [docs/design/04-美术资产管线.md](../../docs/design/04-美术资产管线.md)、[ADR-0004](../../docs/adr/ADR-0004-美术资产来源与LPPL输出物.md)、[ADR-0007](../../docs/adr/ADR-0007-2D写实实验台与分子级3D.md)。
> **状态**：本阶段（规划与设计）只定义目录与流程，脚本在 M0/M1 落地并实测。本目录当前为占位说明。
> **主调**：出版级写实 2D。tikz-chemlab 编译输出物为**主资产**，`@itkdm/open-lab-components` 为辅；**3D 只做分子 / 晶体 / 球棍模型**（3Dmol.js），程序化 3D 器材已降级为可选长线、不进 M1。

## 目的

把上游资产转成产品可用的**写实 2D 实验台器材**：

| 上游 | 许可 | 转换 |
|---|---|---|
| `tikz-chemlab`（LaTeX/TikZ，13 个器材宏） | LPPL-1.3c | `.tex` → standalone PDF → SVG → 分层 SVG/React（**只转译编译输出物**） |
| `@itkdm/open-lab-components`（213+ HTML fragment，化学相关 37 个） | MIT | 无需转换，薄 React 包装；**辅助资产**，与写实主调不冲突时使用 |

> **只转译编译产物、不 fork 源码**：这是本管线不可绕过的第一原则（LPPL 1.3c Clause 1 + ADR-0004）。

## 目录（M0/M1 落地）

```
tools/asset-pipeline/
├── Dockerfile            # texlive + dvisvgm/pdf2svg/poppler/inkscape/svgo
├── build-tikz.sh         # 遍历 13 个宏批量生成 SVG，含参数化变体（主资产）
├── optimize-svg.sh       # svgo 优化 + 字体转曲 + CSS 变量替换
├── check-attribution.py  # 校验每个入库资产都在 ASSETS.csv 有署名
└── README.md             # 本文件：如何重跑、如何新增器材
```

> 早期草案中的 `extract-profile.mjs`（从 SVG 采样轮廓 → `LatheGeometry` 3D 器材）**已随程序化 3D 器材降级为长线而移出主流程**；台账 6.3 规定 3D 只做分子级，不再需要器材 GLB 轮廓。若将来重启该长线，须单独提 ADR。

## 关键流程与命令（示意，待 M0 实测）

```bash
# 1. 构建镜像
docker build -t st-asset-pipeline tools/asset-pipeline/

# 2. 从 CTAN 拉取 tikz-chemlab 源码到构建期临时目录（不入库），生成 13 个器材的 SVG
docker run --rm -v "$PWD/assets:/out" st-asset-pipeline bash build-tikz.sh
#    内部：lualatex --output-format=dvi → dvisvgm --pdf --font-format=woff → svgo
#    → 只把 SVG 写入 assets/labware/，宏包源码与 TeX 中间产物全部留在构建容器内

# 3. 校验署名（CI 也跑）
python3 tools/asset-pipeline/check-attribution.py
```

## 硬约束（不可绕过）

1. **宏包源码不入库、不随产品分发**：`.sty/.tex/Obj.tex` 只在构建期存在；`.gitignore` 已排除 `tools/asset-pipeline/build/` 与 TeX 中间产物。依据 LPPL-1.3c Clause 1（运行 Work 不受限制）+ ADR-0004。
2. **若必须修改宏包源码**：按 LPPL Clause 6 改名 + 附变更日志 + 附完整未修改原件，且放独立 `upstream/` 目录，需新增 ADR。
3. **每个 SVG 入库前**在 `assets/attribution/ASSETS.csv` 登记署名（含 pst-labo 四作者与「仅使用编译输出物」说明）。
4. **字体**：`dvisvgm --font-format=woff` 或 Inkscape 转曲，禁止外部字体依赖。
5. **动态化**：液位 / 颜色 / 倾斜用 `clipPath` + CSS 变量 + `transform`，不为每个状态生成一张 SVG。
6. **写实一致性**：`apparatus` 参数表是单一事实源，同时驱动 SVG 渲染、容器容量与物理约束；不得混入卡通风格资产。
7. **跨平台**：脚本需同时在 **Windows（WSL2 / Docker Desktop）与 Linux** 可跑；路径统一小写、换行符 LF（见 `.gitattributes`）。

## 新增一件器材的步骤

1. 确认上游来源（优先 `tikz-chemlab` 的出版级写实宏；辅助才用 open-lab-components 的 `chemistry/labware`）。
2. 生成 / 挂载 SVG，记录 `baselineY` / `mouthY` / 液位路径到 `apparatus` 参数表。
3. `ASSETS.csv` 增一行署名（含 pst-labo 四作者）。
4. 跑 `schema-validate` + `asset-attribution` + 黄金用例。
5. 写实风格一致性人工复核（与出版级主调不符者退回）。

## 待 M0 验证

- `dvisvgm --pdf` vs `pdf2svg` 对 TikZ 渐变 / 图案的保真度（择优）。
- 液体层能否拆出；不可则用 `clipPath` 遮罩兜底。
- open-lab-components 化学组件的视觉质量与 CSS 变量覆盖度，以及与写实主调的兼容性。
- Kenney 资产包内 LICENSE 是否确为 CC0 1.0（仅取通用音效 / 粒子贴图）。
- **Windows + Linux 双平台**下 Docker 卷挂载与路径换行符一致性。
