# 致谢 · Credits & Acknowledgments

> **ST Crucible / 《ST实验室》** 坚决不重复造轮子。它的能力几乎全部建立在下面这些开源项目与开放数据之上。
> 所有条目均经 GitHub REST API / npm registry / 官方 README 与 LICENSE 原文核实（核实日期 **2026-11-14**）。
> **star 数均为 2026-11-14 动态快照**，会随时间变化，文档引用须带快照日期。
> 许可证核实结论与 F1–F4 事实动作以 [docs/11-问题与决策台账.md](docs/11-问题与决策台账.md) §6 / §7.4 为准。
> **如果它们帮到了你，请去给每个仓库点一个 ⭐** —— 开源生态靠这个运转。

本项目采用「先复用、后创造」原则。下表按用途分组，`许可证` 列是集成时的合规依据；`角色` 列说明是**直接集成**（链接进产品）、**动态链接**（LGPL 库，运行时可替换）、**参考借鉴**（只读设计/源码，不并入构建产物）、**已退场**（早期方案，不进入产品链路）还是**数据**（需独立仓与署名）。

**主项目许可证：LGPL-3.0**（见 `LICENSE` / `LICENSE.GPL-3` / `LICENSE.LGPL-3` / `NOTICE`）。

---

## 1. 定量求解与调度（服务端主链 · 核心复用）

> 台账 2.3 / 3.4 / SP-1：内核为「静态已验算参数 + 动态定量求解」，全部复用现成求解器，不造轮子。

| 项目 | 许可证 | 指标（2026-11-14 快照） | 角色 | 用途 |
|---|---|---|---|---|
| [**SUNDIALS CVODE/CVODES**](https://github.com/LLNL/sundials) — LLNL | **BSD-3-Clause** | ★707 · 活跃 | 直接集成 | 自适应步长 BDF / Adams 刚性 ODE 积分；局部误差估计与 `rtol`/`atol` 容差驱动步长，刚性检测自动切换 —— SP-1「消灭硬编码阈值」的数值基石；Cantera / ChemPy 底层即它 |
| [**SciPy**](https://github.com/scipy/scipy) | **BSD-3-Clause** | ★15,217 | 直接集成 | `solve_ivp` 自适应 RK45 / BDF 参考实现与验证对拍 |
| [**Cantera**](https://github.com/Cantera/cantera) | **BSD-3-Clause**（`License.txt` 原文已核：标准三条款，含 Caltech / Sandia 政府权利声明） | ★885 | 直接集成 | 化学动力学、热力学与输运。**F1**：GitHub API 的 `NOASSERTION` 仅因多版权头未被自动识别，原文已确认可并入 LGPL-3.0 主链 |
| [**ChemPy**](https://github.com/bjodah/chempy) — Björn Dahlgren | **BSD-2-Clause** | ★660 | 直接集成 | 电解质平衡 + 动力学；AI 独立对拍的复算工具 |
| [**pyequion2**](https://github.com/pyequion/pyequion) | **BSD-3-Clause** | ★35 | 直接集成 | 物种分布 / 活度 / pH 求解 |
| [**Reaktoro**](https://github.com/reaktoro/reaktoro) | **LGPL-2.1**（LICENSE 原文核实） | ★224 | **动态链接（主链）** | 化学平衡 / 物种分布 / 热力学。依台账【补正 A】：以**动态链接 + 运行时可替换**形态接入，不把 C++ 源码静态编入主二进制；配齐 §6 义务（显著声明、附 LGPL 全文、允许逆向调试、库可替换、修改版源码可得）。LGPL-2.1 与 GPLv3 兼容 |
| **Significance Manager / simulation LOD** | **借鉴的调度范式（概念，非实测仓库）** | — | 设计范式 | 按「观察者关注度」分配更新预算的游戏引擎成熟范式。**F4**：与上方「已核实库」严格区分，不冒充现成仓库，避免稀释「不重复造轮子」口径 |

> **PHREEQC**：许可证未定，暂不纳入主链，保留观察。SP-1 全链为 BSD-2 / BSD-3 / LGPL-2.1，**不引入 AGPL / GPLv2-only，GPL-3.0 组件因选型决策不纳入**（台账 6.2 / C15）。

## 2. 物性数据

| 项目 | 许可证 | 指标 | 角色 | 用途 |
|---|---|---|---|---|
| [chemicals](https://github.com/CalebBell/chemicals) — Caleb Bell | **MIT** | ★315 | 直接集成 | 化学品物性数据库（临界常数、蒸气压、溶解度等） |
| [thermo](https://github.com/CalebBell/thermo) — Caleb Bell | **MIT** | ★799 | 直接集成 | 热力学与相平衡，纯 Python |
| [CoolProp](https://github.com/CoolProp/CoolProp) | **MIT** | ★1,122 | 直接集成 | 流体热物性（密度、比热、相变） |
| [PyBaMM](https://github.com/pybamm-team/PyBaMM) | **BSD-3-Clause** | ★1,732 | 可选（长线） | 电化学 / 电池模型，电解与原电池实验扩展 |

## 3. 化学信息学（Cheminformatics）

> 用途已收敛：服务于**真实结构解析、结构式绘制与 SMARTS 辅助**，不再承担「上万化合物资料卡检索」主线（台账 1.3 / 2.2）。

| 项目 | 许可证 | 指标 | 角色 | 用途 |
|---|---|---|---|---|
| [**RDKit**](https://github.com/rdkit/rdkit) | **BSD-3-Clause** | ★3,687 | 直接集成（服务端） | SMILES 解析、SMARTS 模板、子结构匹配、描述符、2D 绘制；**作为辅助工具，不再是规模主线** |
| [@rdkit/rdkit (MinimalLib)](https://github.com/rdkit/rdkit/tree/master/Code/MinimalLib) | **BSD-3-Clause** | npm v2026.9.2 · 零依赖 WASM | 直接集成（按需懒加载） | 浏览器端结构式解析与绘制；不进主 bundle |
| [**Kekule.js**](https://github.com/partridgejiang/Kekule.js) — Jiang Partridge | **MIT** | ★280 | 直接集成 | 结构式编辑 / 绘制、SMILES / Molfile / CML IO、子结构搜索；自带 Web Component 与 React 封装 |
| [**SmilesDrawer**](https://github.com/reymond-group/smilesDrawer) — Reymond Group | **MIT** | ★621 | 直接集成 | 轻量 SMILES → 2D 结构式 SVG |
| [openchemlib-js](https://github.com/cheminfo/openchemlib-js) | **BSD-3-Clause** | ★94 | 备选集成 | JS 化学信息学库 |
| [EPAM Indigo](https://github.com/epam/Indigo) | **Apache-2.0** | ★416 | 备选集成 | RDKit 的宽松许可备选 |
| [reactio-draw](https://github.com/Paivel/reactio-draw) | MPL-2.0 | ★36 | 参考借鉴 | 开源化学结构编辑器交互设计 |
| [butlerov](https://github.com/eizemazal/butlerov) | MIT | ★13 | 参考借鉴 | TypeScript + Konva 结构编辑器实现参考 |

## 4. 开放数据

| 数据源 | 许可/性质 | 角色 | 用途与约束 |
|---|---|---|---|
| [**PubChem / PUG-REST**](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest) — NIH/NLM | 免费公开、无需 API Key | **离线候选池（降级）** | 台账 1.3 / 2.2：资料卡即可玩库，**不再以「上万资料卡可查」为验收目标**。PubChem 只作为人工精校时的结构与物性候选来源；限流 ≤ 5 req/s，批量走官方下载通道 |
| [**Open Reaction Database (ord-data)**](https://github.com/open-reaction-database/ord-data) | **CC-BY-SA-4.0**（数据）/ Apache-2.0（脚本） | 数据（**独立仓 + 署名 + SA 隔离**） | 台账 10.4：`data-ord/` 为**独立公开仓库**，主仓仅 submodule 引用；只抽事实性反应式与条件；衍生规则单独署名并保留 SA 声明；不整段复制描述文本。Parquet + Protobuf，最大文件约 40.9 万条 / 105 MB，`DatasetView` 流式读取 |
| [ord-schema](https://github.com/open-reaction-database/ord-schema) | **Apache-2.0** | 设计参考 | 反应数据 schema，作为内部规则表设计参考 |
| [**ORDerly**](https://github.com/sustainable-processes/ORDerly) | **MIT** | ★127 | 离线管线（可选） | ORD 数据抽取与清洗；因产品收敛到真实中学体系，ORD 使用范围已收窄 |
| [Wikidata 化学条目 / ChEBI](https://www.wikidata.org/) | 开放数据 | 数据 | 中文名、别名、分类补充（M2 阶段核实具体条款） |

## 5. 分子 / 晶体 3D 可视化（唯一 3D 用途）

| 项目 | 许可证 | 指标 | 角色 | 用途 |
|---|---|---|---|---|
| [**3Dmol.js**](https://github.com/3dmol/3Dmol.js) — David Koes / Univ. of Pittsburgh | **BSD-3-Clause**（仓库 LICENSE；**F2：GitHub API 为 NOASSERTION，M0 复核**） | ★1,038 | 直接集成 | WebGL 分子 / 晶体 / 球棍模型 3D；支持 pdb / sdf / mol2 / xyz / cif；**官方要求引用其 Bioinformatics 论文**，DOI 于 M0 补齐 |
| [Mol* (molstar)](https://github.com/molstar/molstar) | **MIT** | ★1,043 | 备选 | 大分子 / 晶体可视化 |
| [NGL Viewer](https://github.com/nglviewer/ngl) | **MIT** | ★736 | 备选 | WebGL 分子查看器 |

> 台账 6.3：**3D 只做分子 / 晶体 / 球棍模型**。程序化 3D 器材（Three.js `LatheGeometry`）降级为可选长线、不进 M1，故本版不再把 Three.js / R3F 列为主链 3D 器材方案。

## 6. 前端与渲染（2D 写实实验台）

| 项目 | 许可证 | 用途 |
|---|---|---|
| [React](https://github.com/facebook/react) / [Vite](https://github.com/vitejs/vite) | MIT | UI 框架与构建 |
| [PixiJS](https://github.com/pixijs/pixijs) | MIT | 容器内粒子 / 现象 2D WebGL 渲染（WASM 表现层伴侣） |
| [Zustand](https://github.com/pmndrs/zustand) | MIT | 客户端状态 |
| [Lucide](https://github.com/lucide-icons/lucide) | ISC | UI 图标 |
| [Tabler Icons](https://github.com/tabler/tabler-icons) / [Iconify](https://github.com/iconify/iconify) | MIT | UI 图标备选 |
| [Three.js](https://github.com/mrdoob/three.js) / [React Three Fiber](https://github.com/pmndrs/react-three-fiber) | MIT | **降级**：仅分子级 3D 与可选长线程序化器材，不进 M1 主链 |

> **已删除**：`Yjs`（多人实时协作 / CRDT）—— 台账 9.4「单人 + AI Agent 工作体制，不需要复杂协作机制」，改为轻量存档 + 关键快照时间轴回放；`Service Worker` / `IndexedDB` / 离线规则包 —— 台账 4.2 废弃「断网可玩」。

## 7. 美术资产（重点 · 出版级写实）

> 完整选型、许可证陷阱与转换管线见 [美术资产链调研](docs/research/03-美术资产链.md)、[美术资产管线设计](docs/design/04-美术资产管线.md) 与 [ADR-0004](docs/adr/ADR-0004-美术资产来源与LPPL输出物.md)。

| 资产 | 许可证 | 指标 | 角色 | 用途与关键约束 |
|---|---|---|---|---|
| [**tikz-chemlab**](https://github.com/aihua/tikz-chemlab) / [CTAN](https://ctan.org/pkg/tikz-chemlab) — Aihua Wang | **LPPL-1.3c** | v1.0.0 · ★3 · 已入 TeX Live / MiKTeX | **主资产（输出转译）** | 13 个参数化器材宏（试管 / 烧杯 / 锥形瓶 / 圆底烧瓶 / 量筒 / 滴定 / 蒸馏 / 分液漏斗 / 铁架台…），带液位、倾斜角、颜色、塞子、pH 计、搅拌器等选项，出版级写实线条。**它是 [pst-labo](https://ctan.org/pkg/pst-labo) 的 TikZ 移植**，原作者 Denis Girou / Christophe Jorssen / Manuel Luque / Herbert Voß，一并致谢。**LPPL 第 1 条：运行 Work 不受限制 → 编译出的 PDF/SVG 是输出物，可用于产品；但修改 `.sty/.tex` 源码再分发触发第 6 条（改名 + 变更日志 + 附原始副本）**。策略：「只把编译产物转成 SVG/组件，不改宏包源码」 |
| [**@itkdm/open-lab-components**](https://github.com/itkdm/open-lab-components) — itkdm | **MIT** | ★10 · npm v0.1.1 | **辅助资产** | 零依赖 HTML fragment 组件库，**213+ 组件 / 41 分类**，化学相关 **37 个**：`chemistry/labware` 26 件器材、`chemistry/reaction` 5 个交互、`chemistry/model` 球棍分子与周期表等。台账 5.3：由「主资产」降为**辅**，与出版级写实主调不冲突时才使用 |
| [LabIcons](https://github.com/Center-for-Proteomics-and-Metabolomics/LabIcons) — CPM / 插画师 Manon Zuurmond | **CC-BY-4.0** | ★24 | 资产（**需署名**） | 专业科研器材插画；CC-BY 要求在图注 / 致谢中署名并说明改动 |
| [bioicons](https://github.com/duerrsimon/bioicons) — Simon Dürr | 平台 **MIT**；**单个图标各自 CC0/MIT/CC-BY** | ★1,795 | 资产（**逐个核验许可**） | **平台 MIT 不等于每个图标 MIT**；来源含 Servier（CC-BY 3.0）、DBCLS / TogoTV。必须建逐图标署名清单 |
| [Kenney Assets](https://kenney.nl/assets) — Kenney | **CC0 1.0**（官网 `/license` 页 404，**M0 需包内 LICENSE 复核**） | — | 资产（需复核） | 通用 UI / 音效 / 粒子贴图。**卡通风格不与出版级写实主调混用**，仅取通用音效与粒子贴图 |

> **早期方案已退场**：「双层皮肤可切换」「程序化 3D 器材作主视觉」「Kenney 卡通 2D/3D 器材」均依台账 5.3 / 6.3 废弃；3D 收敛为分子级，不再需要批量化学器材 GLB 资源。

## 8. 教学标准与集成（**整体后置长线，不进 M1–M3**）

> 台账 9.2 / 10.1：教学功能外置给使用方教师，教学层保留愿景但**整体后置到 M4**。下表仅作长线备选登记，**当前不纳入主链验收**。

| 项目 | 许可证 | 角色 | 说明 |
|---|---|---|---|
| [ltijs](https://github.com/Cvmcosta/ltijs) | Apache-2.0 | 长线备选 | LTI 1.3 Advantage Tool |
| [xAPI Spec](https://github.com/adlnet/xAPI-Spec) — ADL / 1EdTech | Apache-2.0 | 长线备选 | 学习行为数据格式 |
| [h5p-standalone](https://github.com/tunapanda/h5p-standalone) | MIT | 长线备选 | H5P 内容离线嵌入 |
| [VChemLab](https://github.com/sdeepak-dev/vchemlab) | MIT · ★0 | 参考借鉴 | 纯静态虚拟化学实验室的教学层数据结构参考（早期项目，不可当成熟依赖） |
| [H5P core](https://github.com/h5p/h5p-php-library) | **GPL-3.0** | **参考（隔离）** | 依台账 6.2 选型决策不纳入主链 |
| [PhET](https://github.com/phetsims) — 科罗拉多大学 | **GPL** | **参考（隔离）** | 同上；官方明确「定制现有 sim 须遵守 GPL」 |

## 9. 已退场 / 仅参考（不链接、不并入构建产物）

| 项目 | 许可 | 状态与理由 |
|---|---|---|
| [**Sandspiel**](https://github.com/MaxBittker/sandspiel) | MIT · ★3,227 | **已退场**。早期作为落沙引擎原型，实读 `crate/src/species.rs` 得出「反应硬编码在 `match` 分支、必须数据驱动」的结论；台账 5.1 / 6.1 确立实验台唯一视图后，**无限画布落沙基座整体废弃**，不进入产品链路。其内部 [PavelDoGreat/WebGL-Fluid-Simulation](https://github.com/PavelDoGreat/WebGL-Fluid-Simulation)（MIT）流体代码一并致谢，仅作历史参考 |
| [The Powder Toy](https://github.com/The-Powder-Toy/The-Powder-Toy) | GPL-3.0 · ★5,411 | **参考（隔离）**。台账 6.2：换 LGPL-3.0 后许可证层面兼容，但依**选型决策**不纳入主链，仅只读设计参考 |
| [tptmp](https://github.com/The-Powder-Toy/tptmp) | **AGPL-3.0** | **严格隔离**。FSF：AGPLv3 与 GPLv3 严格意义不兼容；完全不碰 |
| [Chemistry Development Kit (CDK)](https://github.com/cdk/cdk) | LGPL-2.1 · ★614 | 仅作参考，未纳入选型 |
| [Jmol / JSmol](https://github.com/BobHanson/Jmol-SwingJS) | LGPL-2.1 · ★63 | 仅作参考，未纳入选型 |

## 10. 数据/方法来源（对标与调研）

- NB实验室功能对标资料来自其 [官网](https://www.nobook.com/index.html)、[价格页](https://www.nobook.com/price.html)、[NB化学实验资源页](https://hx.nobook.com/index.html)、应用商店官方描述与百科词条；详见 [NB 对标分析](docs/research/01-NB实验室对标分析.md)。**只采信一级来源**，推广稿中的「几万种物质」「免费版 20%」等未证实表述一律不采信。**本项目不复用其任何代码、素材、商标或界面设计**。
- 检索方法：多引擎聚合（必应中国 / 百度 / 360 / 搜狗）+ GitHub REST API 精确核实 + 官方 README / LICENSE 原文二次核实。

---

## 合规义务速查

| 义务 | 涉及资产 | 落地方式 |
|---|---|---|
| **LGPL-3.0 双文本 + 显著声明** | 主项目 | `LICENSE` + `LICENSE.GPL-3` + `LICENSE.LGPL-3` + `NOTICE`（§4） |
| **动态链接 / 库可替换 / 允许逆向调试 / 附 LGPL 全文** | **Reaktoro (LGPL-2.1)** | 台账【补正 A】§6 义务清单；运行时可替换、不静态编入主二进制；CI 增「动态链接 / 可替换性」检查 |
| 保留版权声明 + 引用论文 | RDKit (BSD-3)、3Dmol.js (BSD-3，M0 复核) | About 页 + `assets/attribution/`；3Dmol.js 引用其 Bioinformatics 论文 |
| **署名 + 声明改动** | LabIcons (CC-BY-4.0)、bioicons 中 CC-BY 图标、tikz-chemlab / pst-labo (LPPL) | 逐资产署名清单；图注 / 致谢页注明 |
| **相同方式共享（SA）** | ord-data (CC-BY-SA-4.0) | **独立公开仓 `data-ord/` 物理分离**，主仓仅 submodule；衍生规则表单独署名并保留 SA 声明；只抽取事实性反应式与条件 |
| **改源码需改名 + 变更日志 + 附原件** | tikz-chemlab 宏包源码 (LPPL-1.3c Clause 6) | 不 fork 源码，只转译编译输出物 |
| **不纳入（选型决策）** | The Powder Toy / PhET / H5P core (GPL-3.0) | 换证后许可证可行，但依台账 6.2 维持「只读参考」；ADR-0001/0005 须写清「为何换证却不引入」 |
| **严格隔离** | tptmp (AGPL-3.0)、GPLv2-only | 完全不碰；CI 白名单禁止 |
| 限流与礼貌抓取 | PubChem PUG-REST | ≤ 5 req/s，批量走官方下载通道 |
| star 标快照 | 全部指标 | 统一标注「2026-11-14 动态快照」，不把动态数当固定事实（F3） |

> 以上为工程判断，**非法律意见**。商业化前建议就 ① CC-BY-SA 数据衍生规则表边界、② LPPL 输出物商用、③ CC-BY 署名充分性、④ 公开点名对标的比较广告合规 四项做一次法务确认。

---

**再次感谢所有维护者与贡献者。** 如果本项目或这份清单对你有用，请给上面这些仓库点 ⭐，并在自己的产品 About 页保留它们的名字。
