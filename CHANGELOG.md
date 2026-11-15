# 更新日志 · CHANGELOG

本项目遵循 [Keep a Changelog](https://keepachangelog.com/) 与语义化版本。当前处于**第二阶段：可行性验证 / M0**，尚无产品代码发布。

## [Unreleased]

### 阶段一 · 决策收口与全仓修订（2026-11-14，v2.0）

**决策阶段**
- 新增 [`docs/11-问题与决策台账.md`](docs/11-问题与决策台账.md)，作为**决策单一事实源**。
- 完成批次一~十一共 **40+ 项裁决**的问询、固定与矛盾销项；含 SP-1 自适应定量调度、A1 换证、实验室规格范式、范式收敛、产品身份、命名避险、路线图、部署 / 教学 / 数据、使命 / 验算 / ORD、噪音幻觉审计与决策收口。
- §7 完成全量**噪音 / 幻觉审计**：作废 N1「每天新体验」噪音、去重 N2–N5 语音重复、修正 P1–P4 归纳偏差、落地 F1–F4 事实动作；用户 11.1 认可。11.2 授权进入修订阶段。

**按台账系统性修订（本轮）**
- **许可证**：主许可证由 Apache-2.0 改为 **LGPL-3.0**（A1）。因 LGPL-3.0 = GPLv3 全文 + 附加权限，`LICENSE` 改为「总说明 + `LICENSE.GPL-3` + `LICENSE.LGPL-3`」双文本体系；`NOTICE` 重写为 LGPL 显著声明 + 库可替换说明；`ADR-0001` 重写并保留变更史。
- **合规边界**：`ADR-0005` 重写为「AGPL / GPLv2-only 严格隔离；GPL-3.0 组件因选型决策不纳入；LGPL 库动态链接准入 + §6 义务」；CI 白名单放行 LGPL-2.1/3.0。Cantera 许可升级为「BSD-3-Clause（原文已核）」，3Dmol.js 保留 M0 复核，star 统一标 2026-11-14 快照。
- **产品身份**：定名 **《ST实验室》/ `ST Crucible`**（规避与竞品中文近似风险，旧名清零）；仓库名保留 `open-chem-lab`；对外按**统一口径 D**三层措辞「当前已独有 / 目标超越维度（规划目标·待达成）/ 合规兜底」，公开点名对标并超越 NB实验室，保留非关联声明，删除「免费版 20%」等未证实表述。
- **范式收敛**：**只做实验台、按实验室规格**；废弃无限画布、Sandspiel 落沙基座、双视图融合、双层皮肤、卡通游戏化主视图；**出版级写实 2D 主视觉，3D 只做分子 / 晶体 / 球棍模型**。
- **架构**：**前后端常驻本地服务器，废弃「断网可玩」**；删除 Service Worker / IndexedDB / 离线规则包 / PWA 离线；服务端承担动态定量求解、物种分布、规则与存档，WASM 收窄为容器内现象即时表现与求解加速；删除 Yjs 多人协作与复杂存档 diff，改轻量存档 + 关键快照时间轴回放；**Win + Linux 双平台兼容**列为硬约束。
- **内核**：从「静态规则表」升级为「**静态已验算参数 + 动态定量求解**」；弱 / 可逆 / 电离 / 水解 / 隐藏反应真实发生；新增 `solution_speciation` 物种分布与 `speciation_timeline` 时间轴；**数值零错为红线、视觉可夸张**；严格真实库、无工坊 / MOD / 自定义物质；1000 个完全仿真反应为下限、长线不封顶。
- **调度**：新增 **ADR-0008 自适应定量调度**（SP-1 四层解耦），`design/07` 性能预算改按 16.7ms 帧预算，规则 schema 增 `rtol/atol/stiffness/significance`。
- **验算**：权威源（NIST / CRC / IUPAC / 课标附录 / 开放教材）+ AI 独立对拍 + 用户人工签核 + CI 黄金用例；每条参数带 `source` / `confidence` / 适用条件。
- **路线图**：全仓**删除时间预算**，改为质量闸门；M0 基座验证 / M1 垂直切片（跑通全链路）/ M2 反应覆盖扩张向 1000 / M3 体验与表现深化 / M4 长线；教学层**保留愿景 · 后置长线**，不进 M1–M3；统一阶段归属，矛盾编号改用 `M-xx` 前缀。
- **i18n**：UI 简中默认 + 英文可选；文档仅简体中文；物质名 / 术语 / 方程式中英双语。
- **ORD**：独立公开仓物理分离，主仓仅 submodule 引用；目录树不再把 `data-ord/` 画在 monorepo 内。
- **硬矛盾销项**：M-01 工期、M-02 阶段归属、M-03 i18n、M-04 ORD 隔离形态、M-05 `assets/structure(s)/` 命名统一为 `structures/`、M-06 未证实数据删除、M-07 分子可视化组件清单统一。
- **工程规范**：`CONTRIBUTING` / `SECURITY` / `docs/README.md` / CI 工作流 / Issue 与 PR 模板 / 资产署名清单 / asset-pipeline 说明按新口径同步。
- **二次矛盾审计**：内部链接、LGPL 双文本、token 泄露、LPPL / GPL / CC-BY-SA 隔离、旧口径回归扫描、CRLF 与 `git diff --check` 全部通过；新增 [`docs/research/data/README.md`](docs/research/data/README.md) 归档声明与 11 条作废口径对照表，两份原始报告头部追加警示块（史料原文不改），`docs/README.md` 索引改标「历史归档 · 不作现行设计依据」，CI 增加归档标识门禁，消除「初版史料被误读为现行设计」的疏漏；`design/01` 图节点 `M3`→`V3D`、`design/03` 引用消歧。完整审计结果见台账 §8.4。

**已核实并保留的调研结论**
- 不存在可直接部署的开源单体虚拟化学实验室；整体型竞品（NB、ChemCollective、Model ChemLab、ChemBox）全部闭源。
- `tikz-chemlab` 为 **LPPL-1.3c**（CTAN 核实，13 个参数化器材宏）；`@itkdm/open-lab-components` 为 **MIT**（213+ 组件，化学相关 37 个）；LPPL 1.3c Clause 1 允许运行 Work，编译输出物可用于产品。
- `sandspiel/crate/src/species.rs` 反应硬编码在 `match` 分支 → 反应规则必须数据驱动（该结论仍成立，但落沙基座本身已退场）。
- LabIcons (CC-BY-4.0)、bioicons（单图标各自许可）、Kekule.js (MIT)、RDKit.js MinimalLib (BSD-3)、PubChem PUG-REST ≤ 5 req/s、ORD 数据 CC-BY-SA-4.0。

### 阶段二 · M0 可行性核验（2026-11-15，进行中）

> 阶段二**不写产品代码，只消解不确定性**。流程基准见 [`docs/12-阶段二开发流程.md`](docs/12-阶段二开发流程.md)，主交付物见 [`docs/research/04-M0验证报告.md`](docs/research/04-M0验证报告.md)。

- **流程**：固定九步闭环 S1–S9（通读 → 核实 → 实测 → 判定 → 登记 → 决策 → 修订 → 复验 → 交付）、质量闸门、偏差分级 L0/L1/L2；调研方法改为「官方 API / LICENSE 原文为主，搜索引擎仅作线索」（长英文聚合检索结果污染，不采信结果页）。
- **实测结论**：M0 十项验证 **6 项通过、2 项部分通过需调整、2 项受限**。四体系定量求解 **14/14 PASS**（稳态中位数 11.5ms）、phreeqpython 官方用例 **9/9 PASS**、AI 独立对拍 **3/3 PASS**；刚性体系 LSODA 262 次 / 1.48ms vs RK45 42500 次 / 259ms（约 175 倍）；500 粒子软件渲染 p95 1.2ms；tikz-chemlab → SVG 纯路径、零字体依赖；Compose 4 服务全 Healthy；axum 16806 rps vs Fastify 4542 rps。原始数据与可重跑脚本见 [`docs/research/data/m0/`](docs/research/data/m0/INDEX.json)。
- **事实销项**：3Dmol.js 许可证 **BSD-3-Clause**（F2 可销）、论文 DOI `10.1093/bioinformatics/btu829`、tikz-chemlab **LPPL-1.3c**、Cantera **BSD-3**、pyequion2 真实仓库 `pyequion/pyequion2`；Reaktoro 确为 LGPL-2.1 但**不在 PyPI**（仅 conda-forge），Kenney 包内 LICENSE（F3）官网 404 未销项。
- **偏差登记**：L2 — phreeqpython 作为电解质/水溶液平衡主引擎显著更优（直接依赖 46→3、能力逐条对口核心需求）、Reaktoro 分发渠道与规划的 pip/Docker 链不一致；L1 — 资产转换命令 `dvisvgm` 双路径失败，实测可行路径为 `lualatex → PDF → pdftocairo -svg`、刚性积分建议以 SciPy LSODA 为主；L0 — 三处文档描述与实物不符（`open-lab-components` 实为 **HTML fragment 库**非 React、简笔示意风与出版级写实冲突、pyequion2 仓库引用写法易误判）。
- **L0 归档一致性修复**（主管直修、不产生新裁决）：按 `docs/12` 第六节「失败项不得静默丢弃 / 脚本与结果必须可复现」，对 `data/m0/` 逐项审计并修复三处**脚本与结果版本错配**——`test_phreeq.py` 早期误用 mol 单位（1/5）与 9/9 结果不符、`golden_cases_probe.json` 第三用例 `buffer_half` 名实不符（改为真正的 HAc/Ac⁻ 等量缓冲）、`test_solver_v3.py` 第 113 行把 dict 当数组切片导致 `except` 分支误追加虚假 FAIL（14/15 → **14/14**）。三组脚本已重写并**实际重跑**，JSON 均为脚本真实产物；报告数字、索引、`INDEX.json` 同步。详见 M0 报告 §4.6。
- **另登记两条实测观察**：ChemPy `root()` 的 `sane=False` 与 `success=True` 可同时出现（初始组成电荷不平衡，M1 正式内容管线须消除）；PHREEQC 缺 Ca 时 `si('Calcite')` 返回 **-999 哨兵值**，CI 须列为非法输入。

### 阶段二裁决收口（2026-11-15，D1–D8 全部固定 ✅）

> 逐字原文与主管登记见 [`docs/11-问题与决策台账.md`](docs/11-问题与决策台账.md) **§9**；总纲见 [`docs/adr/ADR-0009-M0实测驱动的选型调整.md`](docs/adr/ADR-0009-M0实测驱动的选型调整.md)。三批问询后先固定入台账再继续，主管未代裁任何一项。

| # | 级别 | 最终裁决 |
|---|---|---|
| D1 | L2 | **phreeqpython 升为电解质 / 水溶液平衡主引擎**，chempy 降为动力学 + AI 独立对拍 |
| D2 | L2 | **用户自定义方案**：Reaktoro 设计为独立微服务，与主进程实时通讯，使用 gRPC/UDS 确保低延迟（优于主管建议的「移除」，把 conda-only 渠道隔离在单个服务内） |
| D2-补 | L2 派生 | 一般反应 → phreeqpython；多相 / 固相 / 气相、高温高压、剧烈燃烧爆炸、复杂反应 → Reaktoro；「由你设计」 |
| D3 | L1 | **SciPy LSODA/BDF 为刚性积分主力**，CVODES 后置 M1 再评估 |
| D4 | L1 | 网关锁 **Fastify (Node/TS)** |
| D5 | L1 | 资产转换链改 **`lualatex → PDF → pdftocairo -svg → svgo`** |
| D6 | L2 | **先锁单机自托管**，多机 / 公共 Demo 后置 |
| D7 | L1 | 锁 **Python 3.11 + 固定 lockfile** |
| D8 | L1 | `open-lab-components` **仅作 UI / 缩略图**（用户自定义细化），不进写实主视图 |
| 收口 | 流程 | 一次性全量修订并推送 main |

- **S7 全量修订（本轮）**：新增 `ADR-0009`；修订 `CHARTER` 第 5 条、`ADR-0002/0004/0005/0006/0008`、`design/01–05/07`（`04` 与 `tools/asset-pipeline/README.md` 按 D5/D8 **整体重写**）、`research/02/03`、`docs/10` 史料状态注记、`docs/README.md` 索引、`README`、`CREDITS`（补 phreeqpython 主引擎条目）、`NOTICE`（微服务与替换入口）、`CONTRIBUTING`、`SECURITY`、`assets/attribution/`、`ASSETS.csv`、`docs/12` 与本文件；CI 增加阶段二主文档存在性与口径回归检查。
- **主管设计登记（依「由你设计」授权，不产生新裁决）**：主链为唯一事实源入口，`reaktoro-service` 按体系特征按需路由、不并行重复求解；燃烧 / 爆炸拆为「平衡终态 → Reaktoro / 瞬态动力学 → Cantera / 现象表现 → WASM」三层以守住事实零错；单机优先 UDS + protobuf（gRPC 选项保留至未来多机）；进程隔离**不免除** LGPL-2.1 §6 义务，`lgpl-link-check` 改校验服务镜像内的动态链接与可替换性。

### 待办（阶段二 · M0）

- **裁决已全部固定，无未决项**；S7 修订完成后按 S8 复验、S9 推送 main。
- **待补验（受限项）**：Windows / WSL2 / Docker Desktop 双平台最小部署、WASM 工具链与容器内现象本体、3Dmol.js 真实浏览器 WebGL 球棍渲染、Kenney 包内 LICENSE（F3）、CI 全门禁（当前 `license-scan` 等为占位）。
- **待建**：仓库骨架（`schemas/` / `content/` / `packages/` / `deploy/`）与 CI 门禁实体。
- 单机 / 多机 / 公共 Demo 部署形态并入 D6 一并裁决（台账 9.1「到时候再说」）。

---

## 版本说明

- 文档阶段不发布版本号；首个可玩版本为 `v0.1.0`（M1 垂直切片）。
- 内容库独立版本化：`ruleset-core-YYYY.MM.DD`；每条规则带 `rule_revision`，可回滚、可审计。
