# 致谢 · Credits & Acknowledgments

> 本项目**坚决不重复造轮子**。它的能力几乎全部建立在下面这些开源项目与开放数据之上。
> 所有条目均经 GitHub REST API / npm registry / 官方 README 与 LICENSE 原文核实（核实日期 2026-11-14）。
> **如果它们帮到了你，请去给每个仓库点一个 ⭐** —— 开源生态靠这个运转。

本项目采用「先复用、后创造」原则。下表按用途分组，`许可证` 列是集成时的合规依据；`角色` 列说明是**直接集成**（链接进产品）、**参考借鉴**（只读其设计/源码，不并入构建产物）、还是**数据**（需分仓与署名）。

---

## 1. 仿真内核与落沙引擎

| 项目 | 许可证 | 指标（核实） | 角色 | 用途 |
|---|---|---|---|---|
| [**Sandspiel**](https://github.com/MaxBittker/sandspiel) — Max Bittker | **MIT** | ★3,226 · 2026-09 活跃 | 直接集成（fork `crate/`） | L0 粒子/流体/热/压引擎原型。Rust→WASM + WebGL。元素定义集中在 `crate/src/species.rs`，`Species` 枚举 + 每物质 `update_xxx` 函数、`Cell{species,ra,rb,clock}` 结构，是二次开发落点 |
| [The Powder Toy](https://github.com/The-Powder-Toy/The-Powder-Toy) | **GPL-3.0** | ★5,409 · 2026-11 活跃 | **参考借鉴（不链接）** | 反应矩阵、热/压/电耦合、Lua 自定义元素、社区存档工坊的设计参考。GPL 传染，物理隔离 |
| [tptmp](https://github.com/The-Powder-Toy/tptmp) | AGPL-3.0 | — | **参考借鉴（不链接）** | 多人同步思路。AGPL 传染性更强 |

> Sandspiel 内部还采用了 [PavelDoGreat/WebGL-Fluid-Simulation](https://github.com/PavelDoGreat/WebGL-Fluid-Simulation) 的流体模拟代码（MIT），一并致谢。

## 2. 化学信息学（Cheminformatics）

| 项目 | 许可证 | 指标 | 角色 | 用途 |
|---|---|---|---|---|
| [**RDKit**](https://github.com/rdkit/rdkit) — RDKit 社区 | **BSD-3-Clause** | ★3,687 · 2026-11 活跃 | 直接集成 | 服务端分子解析、SMARTS 反应模板、子结构检索、描述符、2D 绘制；PostgreSQL Cartridge 做上万物质检索 |
| [**RDKit.js / MinimalLib**](https://github.com/rdkit/rdkit/tree/master/Code/MinimalLib) (`@rdkit/rdkit`) | **BSD-3-Clause** | npm v2026.9.2 · 零依赖 WASM | 直接集成 | 浏览器端 SMILES 解析、分子绘制、子结构/SMARTS 匹配、指纹、InChI。`RDKit_minimal.{js,wasm,d.ts}` 三文件，可离线自托管。文档见 [rdkitjs.com](https://rdkitjs.com) |
| [EPAM Indigo](https://github.com/epam/Indigo) | **Apache-2.0** | ★416 · 2026-11 活跃 | 备选集成 | 通用化学信息学工具库，含 JS/WASM 绑定与反应支持；作为 RDKit 的宽松许可备选 |
| [**Kekule.js**](https://github.com/partridgejiang/Kekule.js) — Jiang Partridge | **MIT** | ★280 · 2026-11 活跃 | 直接集成 | 结构式编辑/绘制、SMILES/Molfile/CML IO、芳香性/环/手性判别、子结构搜索；自带 Web Component 与 [Kekule-React](https://github.com/partridgejiang/Kekule-React)/Vue 封装，可直接嵌 React |
| [**SmilesDrawer**](https://github.com/reymond-group/smilesDrawer) — Reymond Group | **MIT** | ★621 · 2026-11 活跃 | 直接集成 | 轻量高性能 SMILES→2D 结构式 SVG，适合「资料卡」批量渲染 |
| [openchemlib-js](https://github.com/cheminfo/openchemlib-js) | **BSD-3-Clause** | ★94 · 2026-11 活跃 | 备选集成 | JS 化学信息学库（结构、反应、谱图） |
| [Chemistry Development Kit (CDK)](https://github.com/cdk/cdk) | **LGPL-2.1** | ★614 · 2026-11 活跃 | **参考借鉴** | Java 生态成熟工具包；LGPL 对静态链接有要求，主链不采用 |
| [reactio-draw](https://github.com/Paivel/reactio-draw) | MPL-2.0 | ★36 | 参考借鉴 | 开源化学结构编辑器（React），交互设计参考 |
| [butlerov](https://github.com/eizemazal/butlerov) | MIT | ★13 | 参考借鉴 | TypeScript + Konva 结构编辑器，实现参考 |

## 3. 数值计算与物性

| 项目 | 许可证 | 指标 | 角色 | 用途 |
|---|---|---|---|---|
| [Cantera](https://github.com/Cantera/cantera) | **BSD-3-Clause**（官方口径，LICENSE 文件需在 M0 复核） | ★885 · 2026-11 活跃 | 直接集成（服务端） | 化学动力学、热力学与输运；L2 冷路径的燃烧/平衡积分 |
| [CoolProp](https://github.com/CoolProp/CoolProp) | **MIT** | ★1,122 · 2026-11 活跃 | 直接集成 | 流体热物性（密度、比热、相变） |
| [thermo](https://github.com/CalebBell/thermo) — Caleb Bell | **MIT** | ★799 | 直接集成 | 热力学与相平衡，纯 Python，补齐物性数据 |
| [chemicals](https://github.com/CalebBell/chemicals) — Caleb Bell | **MIT** | ★315 | 直接集成 | 化学品物性数据库（临界常数、蒸气压、溶解度等） |
| [PyBaMM](https://github.com/pybamm-team/PyBaMM) | **BSD-3-Clause** | ★1,732 · 2026-11 活跃 | 可选集成 | 电化学（电池）物理模型，电解/原电池实验扩展 |
| [ReactionMechanismSimulator.jl](https://github.com/ReactionMechanismGenerator/ReactionMechanismSimulator.jl) | **MIT** | ★97 | 可选集成 | 大规模反应动力学机理数值模拟 |

## 4. 开放数据

| 数据源 | 许可/性质 | 角色 | 用途与约束 |
|---|---|---|---|
| [**PubChem / PUG-REST**](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest) — NIH/NLM | 免费公开、**无需 API Key**、无白名单 | 数据 | 上万化合物资料卡（结构、SMILES、InChI、分子式/量、物性、GHS）。**限流 ≤ 5 req/s**，大批量走 [批量下载](https://pubchem.ncbi.nlm.nih.gov/docs/downloads) 或 FTP，不用爬虫硬刷 |
| [**Open Reaction Database (ord-data)**](https://github.com/open-reaction-database/ord-data) | **CC-BY-SA-4.0**（数据）/ Apache-2.0（脚本代码） | 数据（**分仓 + 署名 + SA 隔离**） | 反应生成规则来源。以有机/专利文献反应为主；Parquet + Protobuf，单个大文件达 40.9 万条反应/105 MB，Git LFS 经 Hugging Face 镜像分发。最大文件可用 `DatasetView` 流式读取 |
| [ord-schema](https://github.com/open-reaction-database/ord-schema) | **Apache-2.0** | 直接集成（设计参考） | 反应数据 schema，作为内部规则表设计参考 |
| [**ORDerly**](https://github.com/sustainable-processes/ORDerly) | **MIT** | 直接集成 | ORD 数据抽取与清洗、反应模板基准，离线管线 |
| Wikidata 化学条目 / ChEBI | 开放数据 | 数据 | 中文名、别名、分类、用途补充（M2 阶段核实具体条款） |

## 5. 分子 / 结构可视化

| 项目 | 许可证 | 指标 | 角色 | 用途 |
|---|---|---|---|---|
| [**3Dmol.js**](https://github.com/3dmol/3Dmol.js) — David Koes / Univ. of Pittsburgh | **BSD-3-Clause**（LICENSE 原文：含 GLmol/Three.js/jQuery 代码） | ★1,038 · 2026-11 活跃 | 直接集成 | WebGL 分子/晶体 3D 可视化；支持 pdb/sdf/mol2/xyz/cif；**官方要求引用其 Bioinformatics 论文** |
| [Mol* (molstar)](https://github.com/molstar/molstar) | **MIT** | ★1,043 · 2026-11 活跃 | 备选集成 | 大分子/晶体可视化，更现代 |
| [NGL Viewer](https://github.com/nglviewer/ngl) | **MIT** | ★736 | 备选集成 | WebGL 分子查看器 |
| [Jmol / JSmol (SwingJS)](https://github.com/BobHanson/Jmol-SwingJS) — Bob Hanson | LGPL-2.1 | ★63 | 参考借鉴 | 老牌分子查看器；LGPL，主链不采用 |

## 6. 前端与渲染

| 项目 | 许可证 | 指标 | 用途 |
|---|---|---|---|
| [React](https://github.com/facebook/react) | MIT | ★252k | UI 框架 |
| [Three.js](https://github.com/mrdoob/three.js) | MIT | ★118k | 3D 渲染底座 |
| [React Three Fiber](https://github.com/pmndrs/react-three-fiber) | MIT | ★33.7k | 3D 器材与实验台的 React 封装 |
| [PixiJS](https://github.com/pixijs/pixijs) / [@pixi/react](https://github.com/pixijs/pixi-react) | MIT | ★48.7k | 2D WebGL 粒子/现象渲染 |
| [matter-js](https://github.com/liabru/matter-js) | MIT | — | 器材刚体/碰撞（可选） |
| [Zustand](https://github.com/pmndrs/zustand) | MIT | — | 客户端状态 |
| [**Yjs**](https://github.com/yjs/yjs) — Kevin Jahns / RWTH Aachen | **MIT** | ★23,058 | CRDT 多人协作/存档合并（自行实现，避开 tptmp 的 AGPL） |
| [Godot](https://github.com/godotengine/godot) | MIT | ★120k | 若未来出桌面端的备选引擎 |
| [Vite](https://github.com/vitejs/vite) | MIT | — | 构建工具（M1 阶段锁定版本） |

## 7. 美术资产（重点）

> 完整选型、许可证陷阱与转换管线见 [美术资产链调研](docs/research/03-美术资产链.md) 与 [美术资产管线设计](docs/design/04-美术资产管线.md)。

| 资产 | 许可证 | 指标 | 角色 | 用途与关键约束 |
|---|---|---|---|---|
| [**tikz-chemlab**](https://github.com/aihua/tikz-chemlab) / [CTAN](https://ctan.org/pkg/tikz-chemlab) — Aihua Wang | **LPPL-1.3c** | v1.0.0 (2026-08-03) · ★3 · 已入 TeX Live/MiKTeX | 资产（**输出转译**） | 13 个参数化器材宏（试管/烧杯/锥形瓶/圆底烧瓶/量筒/滴定/蒸馏/分液漏斗/铁架台…），带液位、倾斜角、颜色、塞子、pH 计、搅拌器等选项。**它是 [pst-labo](https://ctan.org/pkg/pst-labo) 的 TikZ 移植**，原作者 Denis Girou / Christophe Jorssen / Manuel Luque / Herbert Voß，一并致谢。**LPPL 第 1 条：运行 Work 不受限制 → 编译出的 PDF/SVG 是输出物，可用于产品；但若修改 `.sty/.tex` 源码再分发，触发第 6 条（改名 + 变更日志 + 附原始副本）**。因此策略是「只把编译产物转成 SVG/组件，不改宏包源码」，详见 [ADR-0004](docs/adr/ADR-0004-美术资产来源与LPPL输出物.md) |
| [**@itkdm/open-lab-components**](https://github.com/itkdm/open-lab-components) — itkdm | **MIT** | ★10 · 2026-10 活跃 · npm v0.1.1 | 直接集成 | 零依赖 HTML fragment 组件库，**213+ 组件 / 41 分类**，其中化学相关 **37 个**：`chemistry/labware` 26 件器材、`chemistry/reaction` 5 个交互（酸碱/电解/平衡/速率/氧化还原）、`chemistry/model` 球棍分子与元素周期表等。提供 Registry JSON、JS API（`lab.mount/updateProps`）、静态站与 MCP Server。Node ≥18 |
| [LabIcons](https://github.com/Center-for-Proteomics-and-Metabolomics/LabIcons) — CPM / 插画师 Manon Zuurmond | **CC-BY-4.0** | ★24 | 资产（**需署名**） | 专业科研器材插画（偏质谱/色谱/分子示意），与 [NIH BioArt](https://bioart.niaid.nih.gov/) 风格一致。CC-BY 要求在图注/致谢中署名并说明改动 |
| [bioicons](https://github.com/duerrsimon/bioicons) — Simon Dürr | 平台 **MIT**；**单个图标各自 CC0/MIT/CC-BY** | ★1,795 | 资产（**逐个核验许可**） | 科学生物/化学 SVG 图标库。**注意：平台 MIT 不等于每个图标 MIT**，README 明确要求逐个引用图标作者与许可；来源含 Servier（CC-BY 3.0）、DBCLS/TogoTV。必须建逐资产署名清单 |
| [Lucide](https://github.com/lucide-icons/lucide) | ISC | ★25,754 | 直接集成 | UI 图标（`lucide-react` ISC） |
| [Tabler Icons](https://github.com/tabler/tabler-icons) | MIT | ★22,647 | 备选 | 6,200+ 图标 |
| [Iconify](https://github.com/iconify/iconify) | MIT | ★6,400 | 备选 | 统一图标框架 |
| [Kenney Assets](https://kenney.nl/assets) — Kenney | **CC0 1.0**（官网 `/license` 页当前 404，M0 需在资产包内 LICENSE 复核） | — | 资产（需复核） | 通用 2D/3D/UI/音效/粒子贴图素材，风格统一。本项目仅用其通用 UI 与音效，**不用其 3D 器材（无对应资源）** |
| [OpenClipart](https://openclipart.org/) / [OpenMoji](https://openmoji.org/) / [FreeSVG.org](https://freesvg.org/) | 公共领域 / CC0（逐项核验） | — | 备选资产 | 通用剪贴画；**逐个核验许可**，非可靠首选 |

> **CC0 化学器材 3D 模型稀缺**：本轮检索到的 3D 玻璃器皿资源几乎全部来自 TurboSquid / CGTrader / Sketchfab 等商业或逐模型授权站点，没有可直接批量集成的 CC0 化学器材 GLB 包。因此 3D 器材采用 **Three.js/R3F 程序化建模**（由 2D 矢量轮廓 + 参数化旋转体/挤出生成），不依赖外部模型，详见 [美术资产管线设计](docs/design/04-美术资产管线.md)。

## 8. 教学标准与集成

| 项目 | 许可证 | 指标 | 角色 | 用途 |
|---|---|---|---|---|
| [**ltijs**](https://github.com/Cvmcosta/ltijs) | **Apache-2.0** | ★373 · 2026-11 活跃 | 直接集成 | LTI 1.3 Advantage Tool，对接 Moodle/Canvas/校园平台 |
| [pylti1.3](https://github.com/dmitry-viskov/pylti1.3) | MIT | ★138 | 备选 | Python LTI 1.3 |
| [lti-1-3-php-library](https://github.com/1EdTech/lti-1-3-php-library) — 1EdTech | Apache-2.0 | ★124 | 备选 | PHP LTI 1.3 |
| [xAPI Spec](https://github.com/adlnet/xAPI-Spec) — ADL / 1EdTech | Apache-2.0 | ★954 | 标准遵循 | 学习行为数据（实验操作过程）上报 |
| [h5p-standalone](https://github.com/tunapanda/h5p-standalone) | MIT | ★346 | 备选 | H5P 内容离线嵌入 |
| [H5P core](https://github.com/h5p/h5p-php-library) | **GPL-3.0** | — | **参考（隔离）** | 若集成 H5P 运行时，须独立进程/页面，不并入主代码库 |
| [VChemLab](https://github.com/sdeepak-dev/vchemlab) | MIT | ★0 · 2026-06 | 参考借鉴 | 纯静态虚拟化学实验室：40 引导实验 / 20 器材 / 118 元素 / 测验与进度，教学层数据结构参考 |
| [PhET](https://github.com/phetsims) — 科罗拉多大学 | **GPL** | — | **参考（隔离）** | 化学小仿真的教学设计；官方明确「定制现有 sim 须遵守 GPL」。仅独立页面原样自托管 |

## 9. 数据/方法来源（对标与调研）

- NB实验室功能对标资料来自其 [官网](https://www.nobook.com/index.html)、[价格页](https://www.nobook.com/price.html)、[NB化学实验资源页](https://hx.nobook.com/index.html)、应用商店官方描述与百度百科词条；详见 [NB 对标分析](docs/research/01-NB实验室对标分析.md)。**本项目不复用其任何代码、素材、商标或界面设计**。
- 检索方法：[multi-search-engine](https://github.com/) 多引擎聚合（必应中国/国际、百度、360、搜狗）+ GitHub REST API 精确核实 + 官方 README/LICENSE 原文二次核实。

---

## 合规义务速查

| 义务 | 涉及资产 | 落地方式 |
|---|---|---|
| 保留版权声明 + 引用论文 | RDKit (BSD-3)、3Dmol.js (BSD-3) | About 页 + `assets/attribution/`；3Dmol.js 引用其 Bioinformatics 论文 |
| **署名 + 声明改动** | LabIcons (CC-BY-4.0)、bioicons 中 CC-BY 图标、tikz-chemlab/pst-labo (LPPL) | 逐资产署名清单；图注/致谢页注明 |
| **相同方式共享（SA）** | ord-data (CC-BY-SA-4.0) | 数据仓与代码仓分离；衍生规则表单独署名并保留 SA 声明；只抽取事实性反应式与条件，不整段复制描述文本 |
| **不链接 / 不合并构建产物** | The Powder Toy (GPL-3.0)、tptmp (AGPL)、PhET (GPL)、H5P core (GPL-3.0) | 仅作只读设计参考或独立自托管页面；多人协作自研（Yjs/MIT） |
| **改源码需改名 + 变更日志 + 附原件** | tikz-chemlab 宏包源码 (LPPL-1.3c Clause 6) | 不 fork 源码，只转译编译输出物 |
| 限流与礼貌抓取 | PubChem PUG-REST | ≤ 5 req/s，批量走官方下载通道 |

> 以上为工程判断，非法律意见。商业化前建议就「CC-BY-SA 数据衍生规则表」与「LPPL 输出物商用」两项做一次法务确认。

---

**再次感谢所有维护者与贡献者。** 如果本项目或这份清单对你有用，请给上面这些仓库点 ⭐，并在自己的产品 About 页保留它们的名字。
