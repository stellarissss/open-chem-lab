# 美术资产转换管线 · Asset Pipeline

> 设计见 [docs/design/04-美术资产管线.md](../../docs/design/04-美术资产管线.md)、ADR-0004、ADR-0007。
> **状态**：本阶段（规划与设计）只定义目录与流程，脚本在 M0/M1 落地并实测。本目录当前为占位说明。

## 目的

把两类上游资产转成产品可用的 2D/3D 器材：

| 上游 | 许可 | 转换 |
|---|---|---|
| `tikz-chemlab`（LaTeX/TikZ，13 个器材宏） | LPPL-1.3c | `.tex` → standalone PDF → SVG → 分层 SVG/React（**只转译编译输出物**） |
| `@itkdm/open-lab-components`（213+ HTML fragment） | MIT | 无需转换，薄 React 包装（约 30 行） |

## 目录（M0/M1 落地）

```
tools/asset-pipeline/
├── Dockerfile            # texlive + dvisvgm/pdf2svg/poppler/inkscape/svgo
├── build-tikz.sh         # 遍历 13 个宏批量生成 SVG，含参数化变体
├── extract-profile.mjs   # 从 SVG 采样轮廓点集 → LatheGeometry profile JSON
├── optimize-svg.sh       # svgo 优化 + 字体转曲 + CSS 变量替换
└── README.md             # 本文件：如何重跑、如何新增器材
```

## 关键流程与命令（示意，待 M0 实测）

```bash
# 1. 构建镜像
docker build -t ocl-asset-pipeline tools/asset-pipeline/

# 2. 从 CTAN 拉取 tikz-chemlab 源码到构建期临时目录（不入库），生成 13 个器材的 SVG
docker run --rm -v "$PWD/assets:/out" ocl-asset-pipeline bash build-tikz.sh
#    内部：lualatex --output-format=dvi → dvisvgm --pdf --font-format=woff → svgo

# 3. 从 SVG 提取 3D 旋转体轮廓
node tools/asset-pipeline/extract-profile.mjs assets/labware/beaker.svg \
     > assets/labware-profiles/beaker.profile.json

# 4. 校验署名（CI 也跑）
python3 tools/asset-pipeline/check-attribution.py
```

## 硬约束（不可绕过）

1. **宏包源码不入库、不随产品分发**：`.sty/.tex/Obj.tex` 只在构建期存在；`.gitignore` 已排除 `tools/asset-pipeline/build/` 与 TeX 中间产物。依据 LPPL-1.3c Clause 1（运行 Work 不受限制）+ ADR-0004。
2. **若必须修改宏包源码**：按 LPPL Clause 6 改名 + 附变更日志 + 附完整未修改原件，且放独立 `upstream/` 目录，需新增 ADR。
3. **每个 SVG 入库前**在 `assets/attribution/ASSETS.csv` 登记署名（含 pst-labo 四作者）。
4. **字体**：`dvisvgm --font-format=woff` 或 Inkscape 转曲，禁止外部字体依赖。
5. **动态化**：液位/颜色/倾斜用 `clipPath` + CSS 变量 + `transform`，不为每个状态生成一张 SVG。
6. **2D/3D 一致**：`apparatus` 参数表是单一事实源，同时驱动 SVG、3D 几何、容量与物理。

## 新增一件器材的步骤

1. 确认上游来源（优先 open-lab-components 的 `chemistry/labware`；组合装置用 tikz-chemlab 宏）。
2. 生成/挂载 SVG，记录 `baselineY` / `mouthY` / 液位路径到 `apparatus` 参数表。
3. 用 `extract-profile.mjs` 生成 3D profile。
4. `ASSETS.csv` 增一行署名。
5. 跑 `schema-validate` + `asset-attribution` + 黄金用例。

## 待 M0 验证

- `dvisvgm --pdf` vs `pdf2svg` 对 TikZ 渐变/图案的保真度（择优）。
- 液体层能否拆出；不可则用 `clipPath` 遮罩兜底。
- open-lab-components 26 件器材视觉质量与 CSS 变量覆盖度。
- Kenney 资产包内 LICENSE 是否确为 CC0 1.0。
