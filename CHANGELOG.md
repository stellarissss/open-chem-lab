# 更新日志 · CHANGELOG

本项目遵循 [Keep a Changelog](https://keepachangelog.com/) 与语义化版本。当前处于**规划与设计阶段**，尚无产品代码发布。

## [Unreleased]

### 阶段一 · 规划与设计（2026-11-14）

**新增**
- 建立仓库 `stellarissss/open-chem-lab`（Apache-2.0，main 分支）
- `CHARTER.md`：固化项目目标、开发规范、四项架构决策、美术资产规范、许可证基线、修订规则
- `README.md` / `CREDITS.md` / `NOTICE`：概览与逐项开源致谢（含许可证与合规义务）
- 调研文档：`research/01-NB实验室对标分析.md`、`02-开源生态全景与选型.md`、`03-美术资产链.md`；前两轮报告与检索原始 JSON 归档于 `research/data/`
- 设计文档 7 份：总体架构、仿真内核与玩法、数据模型与反应规则 Schema、美术资产管线、工程结构与路径、教学层、API 契约与部署（含许可证合规矩阵）
- ADR 7 份：0001 主许可证、0002 混合分层、0003 Web+WASM、0004 美术资产与 LPPL 输出物、0005 GPL/AGPL 与 CC-BY-SA 隔离、0006 反应规则数据驱动、0007 程序化 3D 器材
- `docs/10-完整规划与风险登记册.md`：阶段一主交付物（35+ 条预料中的问题与预案、M0 十项验证、路线图与验收标准、6 项待需求方确认的开放项）
- 工程规范：`CONTRIBUTING.md`、`SECURITY.md`、`.gitignore`、`assets/attribution/`、`tools/asset-pipeline/`、CI 与 PR/Issue 模板

**调研结论（已核实）**
- 不存在可直接部署的开源单体虚拟化学实验室；整体型竞品（NB、ChemCollective、Model ChemLab、ChemBox）全部闭源
- 用户点名的 `tikz-chemlab` 为 **LPPL-1.3c**（CTAN 核实，13 个参数化器材宏）；`@itkdm/open-lab-components` 为 **MIT**（213+ 组件，其中化学相关 37 个）
- LPPL 1.3c Clause 1 允许「运行 Work」，编译输出物可用于产品；修改源码再分发才触发 Clause 6
- Sandspiel 反应逻辑硬编码在 `crate/src/species.rs` 的 `match` 分支 → 必须改为数据驱动（ADR-0006）
- CC0 化学器材 3D 模型稀缺 → 3D 走 Three.js 程序化建模（ADR-0007）
- 补充发现：LabIcons (CC-BY-4.0)、bioicons（单图标各自许可）、Kekule.js (MIT)、ltijs (Apache-2.0)、RDKit.js MinimalLib (BSD-3)、PubChem PUG-REST ≤ 5 req/s、ORD 数据 CC-BY-SA-4.0

### 待办（阶段二 · M0）

- 执行 `docs/10` 第五节的 10 项基座验证
- 按验证结果修订受影响 ADR（Cantera 许可证、tikz 转换方案、网关语言等）
- 建立仓库骨架（`schemas/` / `content/` / `packages/` / `deploy/`）与 CI 门禁
- 确认 `docs/10` 第七节的 6 项开放项

---

## 版本说明

- 文档阶段不发布版本号；首个可玩版本为 `v0.1.0`（M1）。
- 内容规则包独立版本化：`ruleset-core-YYYY.MM.DD`。
