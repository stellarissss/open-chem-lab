# 01 · 架构（唯一技术真理源）

> 本文件是本项目**唯一现行技术与产品真理源**：所有开发所需的定义、技术栈、红线、数据结构、边界与验证原则都在此自包含。
> 开发时只需读本文件 + `02-Roadmap.md`（进度）+ `03-DocDD-Process.md`（流程）+ `specs/`（当前切片）。
> 变更本文件的产品定义、技术栈或红线属重大变更：先说明动机与影响，同步相关文件（敏捷轻量，不套企业审批）。

---

## 一、使命与优先级

> **打造一个专业、好玩的仿真化学实验室。** 只做实验台，一切按实验室规格来；以出版级写实 2D 为主视觉，3D 只用于分子/晶体/球棍模型；以 100% 真实、已验算的化学库为基础，由真实物理化学法则驱动无限组合与涌现。公开点名对标并超越同类闭源产品「NB实验室」，体现在规模、自由度与用户体验上。教学属性是附加内容，后置长线。

冲突时按此优先级裁决：

1. **事实零错为红线**（反应方向/产物/计量/守恒/平衡趋势/pH/浓度数值必须准确；近似规则不得进化学事实层）
2. **红线内好玩优先**（自由探索、错误操作后果、涌现与发现、图鉴与进度、装置建造）
3. **专业与真实**（实验室规格、真实物质与器材、溯源/置信度/适用条件、可自托管）
4. **规模**（可验算物种数 1000+ 为下限，长线不封顶；真实反应由物种网络联立涌现，数量天然远超物种数，规模以前三条为前提）
5. **性能与可维护性**（自适应调度、双平台、契约先行；是达成前四项的手段）

**「超自由」的精确定义**：在 100% 真实、已验算的物质与器材之上，由真实物理化学法则驱动的无限组合与涌现。**绝不**接受虚构物质、用户自制物质、自定义规则、MOD 或规则包工坊。

---

## 二、产品定义与边界

| 维度 | 定义 |
|---|---|
| 名称 | 《ST实验室》/ `ST Crucible`；仓库 `open-chem-lab`（仓库名 ≠ 产品名） |
| 形态 | 前后端常驻的本地服务器部署，浏览器访问；硬约束 **Windows + Linux 双平台兼容** |
| 主视图 | **实验台唯一视图**，按实验室规格摆放与连接真实器材；**无**无限画布/落沙沙盒/双视图 |
| 视觉 | 出版级写实 2D（`tikz-chemlab` 编译 SVG 为唯一主资产）；`open-lab-components` 仅作 UI/缩略图；3D 只做分子/晶体/球棍（3Dmol.js） |
| 核心玩法 | 取真实器材与药品 → 任意组合 → 参数调节 → 服务端动态定量求解 → 容器内现象表现 → 物种面板/微观视图/时间轴回放；错误操作后果可零风险重现 |
| 化学库 | 严格真实库；规模基线 **1000+ 可验算物种**（含弱/可逆/电离/水解所需的物种与平衡常数），长线不封顶；真实反应由物种网络联立涌现（单 USGS `minteq.dat` 即含约 1000 物种），凡进资料卡必须可玩 |
| 内容组织 | 主线按「化学体系/玩法/器材」组织，覆盖全人类化学体系；课标/教材仅作**可选检索标签**，不设教学功能 |
| 底线 | 开源 LGPL-3.0、可自托管、无会员墙；前后端缺一不可，**废弃断网可玩**；无破解/绕授权/逆向内容 |
| 教学层 | 附加内容、后置长线，不进前期阶段验收；教学由使用方教师承担 |
| 对标 | 公开点名「对标并超越 NB实验室」，同时声明「独立开源实现、与其无关联无背书」；只用一级来源数据，禁用未证实宣传数字 |

**科学边界与求解出口（诚实声明）**：「任意两种物质混合生成什么」在化学上不可判定（取决于温度/浓度/溶剂/pH/压强/相态/催化剂/光照/时间/容器）。求解通过 `st.solution_speciation.v1` 的 `outcome` 如实返回三种状态：覆盖范围内给出定量解（`solved`）；条件在事实层覆盖范围外给出「当前条件下无明显变化」（`no_significant_change`，合法结论）；数值不收敛或活度模型超出适用域给出标注置信度的降级提示（`degraded`）。三种出口各自对应真实计算状态，均进入补体系日志。已制作的体系必须既好玩又科学、零科学性错误。

---

## 三、架构总览

```mermaid
flowchart TB
  subgraph C[浏览器 · 表现层（固定 60fps）]
    UI[React + TS<br/>实验台/物种面板/微观视图/时间轴/图鉴]
    W[WASM 容器内现象渲染<br/>液体·气泡·沉淀·火焰·飞溅 + 求解加速]
    R2[写实 2D 器材 SVG · tikz-chemlab 输出物]
    V3D[3Dmol.js 分子·晶体·球棍]
    UI --> R2
    UI --> V3D
    UI <-->|物种快照 + 时间戳 + 现象指令| W
  end
  subgraph S[服务端 · 常驻（本地服务器，唯一事实源）]
    GW[API 网关 Fastify REST/WS<br/>鉴权·会话·限流]
    SCHED[自适应调度器<br/>关注度分数·16.7ms 帧预算·事件唤醒]
    SOLVE[动态定量求解<br/>phreeqpython主/SciPy LSODA/chempy对拍<br/>Cantera/reaktoro-service(UDS)]
    SPEC[物种分布/平衡/动力学/pH/活度/电离度]
    RULES[(真实反应库<br/>静态已验算参数+条件+来源/置信度)]
    TL[(关键快照时间轴 + 轻量存档)]
    GW --> SCHED --> SOLVE --> SPEC
    SOLVE <--> RULES
    SPEC --> TL
  end
  subgraph D[内容与资产]
    CONTENT[人工精校真实反应库<br/>权威源→AI 对拍→用户签核→黄金用例]
    TP[data-thirdparty 统一独立仓<br/>ord CC-BY-SA / cameo 事实性结论]
    ART[tikz-chemlab 输出物(主) · open-lab-components(UI/缩略图)]
    CONTENT --> RULES
    TP -.事实性数据.-> RULES
    ART --> R2
  end
  W <-->|现象指令/快照/操作事件| GW
```

### 分层职责与性能约束

| 层 | 位置 | 职责 | 关键约束 |
|---|---|---|---|
| 内容层 | 仓库 / 独立仓 | 真实反应参数、器材参数、资产署名 | 离线、可 diff / 回滚 / review |
| 静态参数层（事实层） | 服务端内存 / PG | Ka/Kb/Ksp/E°/ΔG、动力学、计量、适用条件，带 source/confidence | 只读、版本化、零错签核 |
| 动态求解层 | 服务端 worker | 物种分布、平衡、pH/浓度/活度、电离/水解、热效应；隐藏反应真实发生 | 独立 worker，不占帧预算 |
| 调度层 | 服务端 | 关注度分数、帧预算配额、事件唤醒、稳态冻结与缓存 | 16.7ms 帧预算 |
| 表现层 | 浏览器 WASM/SVG | 容器内现象、写实 2D、分子级 3D、物种面板/时间轴 | 固定 60fps，与求解耗时彻底解耦 |
| 教学层 | 长线 | 附加内容，后置长线 | 不进前期阶段验收 |

**关键解耦**：求解器只认数值、不认渲染；WASM 只认现象 ID、不认分子；二者通过 `st.phenomenon.v1` 协议通信，渲染器与求解器可独立替换。

**现象由状态派生（涌现可玩的关键）**：一切现象由 `solution_speciation` 的客观状态经 `st.phenomenon.v1` 的 `trigger`（可观测状态触发器）派生——pH 驱动指示剂按 Henderson–Hasselbalch 连续混色、温度驱动沸腾/放热现象、物种浓度积驱动析出。事实层只提供物性参数（指示剂 pKa 与两形态色、Ksp、反应焓），表现层按状态实时计算现象，手写规则与物种网络涌现的反应在此一视同仁：倒入什么、求解算出什么状态，就看到什么现象。指示剂变色区间由其 pKa±1 派生，随求解 pH 渐变而非阈值跳变。

**明确不采用的部件（勿留死代码）**：Service Worker、IndexedDB、离线规则包、PWA 离线、无限画布/落沙网格、双视图、Yjs 多人协作、复杂存档 diff、规则包工坊/自定义物质编辑器、程序化 3D 器材。

---

## 四、技术栈与求解链（全部复用成熟开源，不造轮子）

| 层 | 选型 | 许可 |
|---|---|---|
| 语言 | TypeScript 5.x（前端/网关）、Rust（WASM）、**Python 3.11 + 固定 lockfile**（求解） | — |
| 包管理 | pnpm workspace / Cargo / uv·Poetry，lockfile 入库 | — |
| 前端 | React + Vite + Zustand + PixiJS | MIT / ISC |
| **定量求解** | **phreeqpython（水溶液平衡主引擎，Apache-2.0）**、SciPy LSODA/BDF（刚性积分，BSD-3）、chempy（对拍，BSD-2）、Cantera（燃烧/爆炸瞬态动力学，BSD-3）、pyequion2（BSD-3）、**reaktoro-service 独立微服务**（多相/高温高压/燃烧爆炸平衡终态，LGPL-2.1） | 全链兼容 LGPL-3.0 |
| 化学结构 | RDKit / Kekule.js / SmilesDrawer / RDKit.js | BSD-3 / MIT |
| 物性 | chemicals / thermo / CoolProp | MIT |
| 分子 3D | 3Dmol.js（唯一 3D 用途） | BSD-3 |
| WASM | wasm-pack + wasm-bindgen（容器内现象渲染） | — |
| 网关 | **Fastify (Node/TS)**（REST + WS + 鉴权） | MIT |
| 数据库 / 缓存 | PostgreSQL（可选 RDKit Cartridge）/ Redis | — |
| 美术资产 | tikz-chemlab（写实主资产，输出物）、open-lab-components（仅 UI/缩略图）、LabIcons、bioicons | LPPL / MIT / CC-BY / CC0 |

**求解职责二分**：phreeqpython 承担一般水溶液/电解质体系（绝大多数反应）；reaktoro-service 承担多相/固相/气相、高温高压、复杂体系平衡终态；燃烧/爆炸的**瞬态动力学**由 Cantera 负责。**主链是唯一事实源入口**，两服务不并行重复求解同一体系。数值步长由 SciPy LSODA/BDF 的局部误差 + `rtol`/`atol` 决定、内置刚性检测自动切 BDF↔Adams，**无硬编码时间阈值**（CVODES 为可选加速）。

**自适应调度**：关注度分数 = `视野内 + 刚被操作 + 有可见现象 + 时间轴聚焦`；高分高频高精度、低分降频/冻结/缓存；按 16.7ms 帧预算动态配额。验收：焦点内数值零错、帧率恒 ≥ 60fps、焦点外算力随关注度单调下降、新增体系无需改调度代码。

**刻意不引入**：Neo4j、Kafka、Elasticsearch、Kubernetes、独立 ML 服务、Nx/Turbo、Yjs、Service Worker/IndexedDB —— 单机自托管是硬门槛，每多一个组件都增加部署与运维成本。

---

## 五、数据模型（事实层核心）

### 5.1 核心实体（单一事实源：`schemas/`）

| 实体 | 作用 | 关键字段 |
|---|---|---|
| `compound` | 可玩物质卡（凡入库必须可玩） | `names`(中英双语)、`formula`、`properties`、`safety`、`playable:true`、`source`、`confidence`、`review` |
| `apparatus` | 实验台器材（参数单一事实源，驱动 2D SVG/容量/物理约束） | `capacity_mL`、`graduations`、`max_temp_K`、`sealable`、`asset`、`physics` |
| `reaction_rule` | 条件化真实反应（核心） | `equilibrium`/`kinetics`/`thermo`(定量)、`applicability`、`numerics`、`effects`、`source`/`confidence`/`ai_crosscheck`、`data_class` |
| `solution_speciation` | 每容器隐藏化学态（不可见反应也真实发生） | `species[]`、`ph`、`ionic_strength`、`temperature_K`、`equilibria`、`hidden_reactions`、`outcome`（三态出口）、`confidence`、`indicators`（实际加入的指示剂，供现象派生）、`physics_note` |
| `speciation_timeline` | 关键快照时间轴 | `keyframes[]`、`curves`、`ruleset_version` |
| `phenomenon` | 12 类现象注册表（`st.phenomenon.v1` 指令） | `type`、`trigger`（可观测状态触发器）、`关联物理量` |
| `save` | 轻量存档（无网格/RLE/Yjs） | `apparatus[]`、`substances[]`、`timeline_ref`、`ruleset_version` |

**三类数据分层**：`fact`（计量/热力学/动力学，零错签核）、`presentation`（颜色/焰色/外观，可夸张但标来源，不受零错红线）、`safety`（GHS/危害，严谨签核，驱动错误操作后果）。

**正确性护栏（CI 必跑）**：计量守恒（元素原子数 + 电荷双核算，构建期轻量解析简式）、条件互斥（同一反应物集合+条件不得有两条 verified 规则，作用域限于表现/安全效果层条目，不约束平衡网络的重叠物种反应）、置信度闸门（非 verified 不进沙盒、ml_guess 禁）、来源/对拍/签核完整性、黄金用例集（中和/制氧/置换/沉淀/电解/弱酸电离/水解/缓冲/络合等逐条断言）、`applicability` 必填、ORD 衍生规则带 CC-BY-SA 溯源。参数变更走 `rule_revision`、禁原地覆盖、可回滚。

### 5.2 权威数据供应链（构建期固化，运行时零网络依赖）

```
权威源层(构建期离线快照) → 候选池层(confidence: extracted)
  → AI 独立对拍(解析解 + chempy/phreeqpython/Cantera) → 用户签核(verified)
  → CI 黄金用例 → 静态参数层(版本化 YAML/JSON 物化, content/rules/)
  → 服务端动态求解 → 内容寻址键缓存(solve_cache, 稳态复用)
  未命中 → uncovered_log(按频次补体系，人工精校回到候选池)
```

| 数据域 | 具体源 | 准入 |
|---|---|---|
| 水溶液 logK（主源） | USGS PHREEQC `wateq4f.dat` / `minteq.dat`（稀区，Davies/延展 Debye–Hückel，本期）/ `pitzer.dat`（浓区与高离子强度，长线启用）（公共领域） | 物化层主源；按离子强度选用对应活度模型。本期中和体系以 `minteq.dat.snapshot` 为求解主库（含乙酸解离，`wateq4f.dat.snapshot` 并存签核），二者均为 `.dat` 权威源离线快照 |
| 金属络合稳定常数 | NIST SRD46 SQL.zip（官方标 known errors、已停更） | 待签核候选，禁直通 |
| 燃烧/高温热化学 | NIST–JANAF SRD13 | 候选（替代红线库 Burcat） |
| 动力学 Arrhenius | NIST Kinetics SRD17 / Solution SRD40 | 候选 → Cantera |
| 焰色/发射谱 | NIST ASD SRD78 | 表现层 |
| 物性/GHS | PubChem PUG-REST（≤5 req/s） | 构建期离线快照 |
| 错误操作后果 | CAMEO 反应基团/相容性图 | 只抽事实性结论、隔离仓 |
| 高精度热化学 | ATcT v1 API（受限） | 留复跑路径 |

**数值真理源与派生**：权威源 `.dat` 快照是热力学数值（logK/ΔH）的唯一数值真理源；`compound`/`reaction_rule` 的 JSON 卡是从快照派生的精校层（携带适用条件、来源、置信度与表现层参数），由 `tools/materialize-rules.py` 构建期物化为运行时 ruleset。二者以 `source.sha256` 与 `ruleset_version` 对齐，避免双真理源。签核粒度为**体系级**：某体系的黄金用例集全绿且数值回指权威源快照，即该体系签核通过；新增数值沿用同一机制，无需逐数值人工重复裁决。

**准入判据**：①宽松许可可进 LGPL 主链 ②可自托管、可机读批量 ③带版本/快照日/可溯源 ④不引入商业数据库/不引入精度分级；官方声明 AS IS 的须对拍签核。每条快照记录 `endpoint / license / snapshot_date / sha256`。

**缓存**：物化层构建期 O(1) 查表（免计算）；求解缓存用内容寻址键 `sha256(canonical(system) + canonical(conditions) + solver_ver + ruleset_ver)`，失效由数据快照/求解器/ruleset 三版本驱动，复用 `solve_cache`、**零新中间件**。缓存价值在免计算与可复现，不在提速。

### 5.3 求解口径与状态派生（已裁决的实现决策）

以下决策已由切片 003 落地并经用户裁决，是现行口径，开发须遵循：

- **体积归一（pH 是强度量）**：溶液 pH 只取决于浓度（总物质的量 ÷ 总体积），与绝对体积无关。求解按各物质体积折算实际摩尔数后归一到 phreeqpython 的固定 1 kg 水基准；缺此归一会把「0.1 M × 2 L」错算成 0.2 M。固化为不变量断言（体积无关性、浓度十倍 pH 降一）。
- **指示剂为痕量探针**：指示剂（酚酞/甲基橙）是被动探针，不参与稀区平衡求解（权威源 `.dat` 未定义其平衡）；求解输出 `indicators` 记录实际加入的指示剂，现象层只对其派生变色——倒什么看什么，且不以伪元素破坏求解收敛。变色按 Henderson–Hasselbalch 随 pH 连续混色，不设阈值跳变。
- **热效应按混合总质量**：绝热温升 `ΔT = Q /(m_total · cp)` 按混合后总质量折算（固定 1000 g 会把 1 L+1 L 的温升高估一倍）。
- **浓硫酸稀释与飞溅分层**：稀释焓 ΔH = -95.28 kJ/mol（液相生成焓差 `-909.27 - (-813.99)`，工程通用值 -95 交叉印证），签核入 `sulfuric_acid_dilution` 规则。**事实层**：ΔH 是状态函数、与加入方向无关，故浓硫酸入水与水入浓酸的整体温升相同；**安全层**：飞溅由可观测的加入顺序派生——水入浓酸时水密度小浮于酸面、界面薄层闪沸裹挟酸液飞溅，酸入水时酸沉底、热量分散不飞溅；飞溅强度是表现层近似，不进化学事实层。浓硫酸属浓区体系，不进稀区平衡求解，长线由 `pitzer.dat` 承担。
- **活度域出口**：稀区（I < 0.5 mol/L）用 Davies/延展 Debye–Hückel 给出定量解；越界或不收敛走 `outcome: degraded` 附置信度；覆盖范围外走 `no_significant_change`（合法结论）。浓区数值由长线 `pitzer.dat` 承担。

---

## 六、工程结构（pnpm Monorepo）

```
open-chem-lab/
├── AGENTS.md  README.md  CREDITS.md  CONTRIBUTING.md  SECURITY.md
├── LICENSE  LICENSE.GPL-3  LICENSE.LGPL-3  NOTICE
├── schemas/            # JSON Schema 单一事实源(各语言类型由此生成)
├── content/            # 人工精校真实反应库(核心自研资产)
│   ├── rules/          # 按体系分目录的 YAML 参数
│   ├── golden-cases/   # 数值零错黄金用例
│   └── ai-crosscheck/  # AI 独立对拍记录
├── packages/
│   ├── protocol/       # TS：现象协议/存档/时间轴/类型(最底层，不依赖任何包)
│   ├── solver-worker/  # Python 3.11 动态定量求解（常驻 worker 进程）
│   ├── reaktoro-service/ # 独立微服务(conda + UDS/protobuf)
│   ├── scheduler/      # 自适应调度
│   ├── speciation/  reaction-library/  phenomenon/  apparatus/
│   ├── wasm-view/      # Rust→WASM 容器内现象
│   ├── web-ui/         # React+Vite 实验台/面板/时间轴/图鉴
│   ├── gateway/        # Fastify REST+WS
│   └── save/  data-pipeline/  shared/  (teaching/ 长线)
├── tools/asset-pipeline/   # 美术资产转换
├── tools/materialize-rules.py      # 构建期物化 content/rules → content/materialized
├── tools/doc-hygiene-check.py      # 文档纯净门禁（单一状态 + 无过程痕迹 + 正向规格）
├── assets/                 # 资产产物 + attribution/
├── deploy/                 # docker-compose / Dockerfile / .env.example / README-windows.md
├── tests/                  # e2e(部署可达) / golden-cases / schema-validate / evidence-check / license-scan / lgpl-link-check
└── docs/                   # 本真理源 + Roadmap + DocDD + specs/
```

**依赖规则**：`protocol` 最底层不依赖任何包；`solver-worker`(Python) 与 `wasm-view`(Rust) 经协议 JSON 通信、互不 import；`web-ui` 不直连求解库、一律经 gateway；任何包不得引入 AGPL/GPLv2-only 依赖；`content/` 是数据、由 reaction-library 运行时加载、不被代码 import。

**包名以本节为准**：本目录树是目标态蓝图与现行实现的总和。实现时若需偏差（改名/新增/省略/调整），先询问用户并同步本节，**不得擅自偏离**——真理源与仓库现实的一致性靠这条规则保证，无需事后核对。

**部署（单机自托管，Docker Compose）**：最小部署 = `web + gateway + solver-worker + postgres + 本地卷`；reaktoro-service 为可选占位服务（显式 `--profile reaktoro` 启用），经本机 UDS/回环通讯；前后端常驻。双平台硬约束：`.gitattributes` 强制 LF、路径统一小写 snake_case、卷挂载/端口可配、容器非 root、TeX 转换全程在 Docker 内。运行期可无外网，但本地服务器必须在线（**不提供断网可玩**）。

---

## 七、红线与验证原则

### 7.1 不可协商红线（违反即推倒重来）

1. **事实零错**：方向/产物/计量/守恒/平衡趋势/pH/浓度数值准确；近似只作用于视觉/时间尺度/夸张，不进事实层。
2. **真实库、无工坊**：不虚构物质、不做自定义规则/MOD/工坊。
3. **许可证边界**：主代码 LGPL-3.0（`LICENSE` + `LICENSE.GPL-3` + `LICENSE.LGPL-3` 三文件 + `NOTICE` 显著声明）；宽松与 LGPL 组件按义务接入；**AGPL(tptmp)、GPLv2-only 严格隔离**；GPL-3.0 组件（The Powder Toy/PhET/H5P）依选型不纳入主链、只读参考；**CC-BY-SA 数据（ORD/CAMEO）独立仓 `data-thirdparty/` 物理分离**，主仓仅 submodule；**LPPL 只转译 tikz-chemlab 编译输出物、宏包源码不入库**。
4. **Reaktoro LGPL-2.1 §6/§4 义务**：独立微服务、动态链接、运行时可替换、显著声明、附 LGPL 全文、允许逆向调试、修改版源码可得；进程隔离不免除义务。
5. **前后端常驻、双平台兼容**；废弃断网可玩。
6. **不重复造轮子**：动手前先搜开源成品与官方文档，能复用即复用；困难/法律/坐标类问题先查证再给方案。

### 7.2 验证原则（敏捷轻量）

- **任务内按需验证、产品级门禁由 CI 统一守门**：单个任务收尾只跑与该任务相关的最小充分证据，不要求每个任务跑全套；质量由「数值零错红线 + CI 强制门禁 + 用户随时可打断」保障，验证结果由测试产物与 git log 承载。
- **已接入 CI 的强制门禁**：构建（`build`/`typecheck`）、内容 schema 与护栏（`schema-validate`）、美术资产署名与存在性（`asset-attribution`：逐 SVG 署名、许可白名单、纯 path、器材卡 asset 路径闭合）、物化幂等、`golden-cases`（数值零错 + 依赖指纹）、证据自证（`evidence-check`）、文档纯净（`doc-hygiene-check`）、依赖许可证（`license-scan`）、文档结构与合规红线、部署可达（`e2e`）。随切片继续接入：`lgpl-link-check`、`rule-lint`、`dual-platform`。
- **证据自证**：凡验收声称用某工具独立对拍，须在代码中真实调用、运行时打印版本与调用指纹、CI 校验一致；黄金用例期望标注来源（独立对拍/权威源快照/解析式）并锚定权威源哈希；关键量纲不变量（体积无关性、浓度十倍 pH 降一）固化为断言（流程见 `03-DocDD-Process.md` 第四节）。

### 7.3 对外口径（不可拆分的三层）

| 层次 | 内容 | 标注 |
|---|---|---|
| 当前已独有 | 开源 LGPL-3.0 + 可自托管 + 无会员墙 | 已具备 |
| 目标超越维度 | 规模（1000+ 可验算物种 vs NB 化学单科近 200 实验）、自由度（真实法则无限组合+定量求解）、用户体验（错误操作后果/物种面板/时间轴/数值零错/写实实验台） | 规划目标·待达成，逐项标状态、不冒充既成事实 |
| 合规兜底 | 点名「对标并超越」+「独立开源实现·无关联无背书」声明；NB 侧只用一级来源，禁用「几万种物质」「免费版 20%」未证实表述 | 强制 |

> 法律边界：本项目合规分析为工程判断、非法律意见。商业化前就 CC-BY-SA 衍生边界、LPPL 输出物商用、CC-BY 署名充分性、比较广告合规四项做法务确认。

### 7.4 已知限制（当前形态可接受、条件变化时须修）

- **WS 现象通道按房间全局广播**：gateway 的 `phenomenon` 订阅把热效应指令推给所有订阅者，指令自带 `container_id` 但前端按"最新一条"渲染、不按容器过滤。当前 compose 仅回环发布、面向单机单用户，无实际串扰触发路径；**进入多用户/多实验台形态前，须改为按 `container_id` 定向推送或前端按当前容器过滤**，否则 A 的错误操作现象会显示在 B 的容器上。属体验隔离限制，不影响数值零错红线。
