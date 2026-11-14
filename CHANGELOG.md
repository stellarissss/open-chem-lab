# 更新日志 · CHANGELOG

本项目遵循 [Keep a Changelog](https://keepachangelog.com/) 与语义化版本。当前处于**规划与设计阶段**，尚无产品代码发布。

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

### 待办（阶段二 · M0）

- 执行 `docs/10` 的 M0 验证清单（含 **Windows + Linux 双平台**最小部署验证）。
- 按验证结果修订受影响 ADR：3Dmol.js 许可证 (F2)、Kenney 包内 LICENSE、网关语言选型。
- 建立仓库骨架（`schemas/` / `content/` / `packages/` / `deploy/`）与 CI 门禁。
- 单机 / 多机 / 公共 Demo 部署形态在阶段二决策（台账 9.1「到时候再说」）。

---

## 版本说明

- 文档阶段不发布版本号；首个可玩版本为 `v0.1.0`（M1 垂直切片）。
- 内容库独立版本化：`ruleset-core-YYYY.MM.DD`；每条规则带 `rule_revision`，可回滚、可审计。
