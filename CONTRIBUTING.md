# 贡献指南 · CONTRIBUTING

欢迎参与。本项目**第一阶段（规划与设计）已收口、第二阶段（可行性验证 / M0）已于 2026-11-15 结束**，正进入阶段三 M1 垂直切片（尚无产品代码）。工作体制为**单人 + AI Agent**，贡献者协议从简，不设复杂协作机制（台账 9.4）。阶段二实测证据与复跑步骤见 [`docs/research/04-M0验证报告.md`](docs/research/04-M0验证报告.md) 与 [`docs/research/data/m0/RERUN.md`](docs/research/data/m0/RERUN.md)。

贡献前请先读：

1. [docs/11-问题与决策台账.md](docs/11-问题与决策台账.md) — **决策单一事实源，先读**
2. [CHARTER.md](CHARTER.md) — 使命、开发规范、固定裁决（**不可绕过**）
3. [docs/README.md](docs/README.md) — 文档索引
4. [docs/adr/](docs/adr/) — 关键决策及理由
5. [CREDITS.md](CREDITS.md) / [NOTICE](NOTICE) — 许可证基线与 LGPL 显著声明

## 当前最需要的贡献

| 类型 | 说明 |
|---|---|
| **真实反应内容精校** | `content/rules/` 中已验算的真实反应参数（Ka/Kb/Ksp/E°/ΔG、热物性、动力学），带**权威源 + 适用条件 + AI 对拍记录 + 人工签核** —— **最高价值** |
| M0 验证 | `docs/10-完整规划与风险登记册.md` 的 M0 验证清单，含 Win / Linux 双平台 |
| 美术资产 | tikz-chemlab 编译输出物 → SVG 转译、写实风格统一、逐资产署名清单整理 |
| 课标知识点整理 | 按课标知识点组织反应覆盖、标注多版本教材对应章节（**内容组织，不是内置教学功能**） |
| 文档 | 纠正事实、补充一级来源、术语双语 |

## 规范

### 提交

- Conventional Commits：`feat(rule): …` / `fix(solver): …` / `docs: …` / `content: …` / `chore: …`
- 分支：`feat/*`、`fix/*`、`docs/*`、`content/*`；`main` 受保护，PR 需通过 CI 门禁。
- **禁止**提交任何密钥、token、`.env` 或 ORD 原始数据文件。

### CI 门禁（PR 必过）

- `license-scan`：依赖许可证白名单（MIT / BSD-2 / BSD-3 / Apache-2.0 / ISC / CC0 / CC-BY / **LGPL-2.1 / LGPL-3.0**），**AGPL 与 GPLv2-only 直接失败**；GPL-3.0 组件依选型决策不纳入主链，若拟引入必须先提 ADR。
- `lgpl-link-check`：校验 LGPL 库为**动态链接 + 运行时可替换**、随附许可证全文与显著声明（§4/§6 义务）。
- `schema-validate`：`content/` 全部 YAML/JSON 符合 `schemas/`。
- `rule-lint`：计量守恒、条件互斥、置信度闸门、来源完整性、适用条件完整性。
- `golden-cases`：教材代表实验断言（中和、制氧、置换、沉淀、电解、弱酸碱电离、水解…）—— **数值零错红线**。
- `asset-attribution`：每个入库资产在 `ASSETS.csv` 有记录；仓库内不含 tikz-chemlab 宏包源码。
- `build`：pnpm build + wasm-pack + Docker 镜像（M0 起）。

### 内容（真实反应）贡献要求

**严格只做真实库**：不接受虚构物质、用户自制物质、自定义规则、MOD 或规则包工坊（台账 5.4 / 6.4）。

每条参数必须包含：

```yaml
confidence: verified          # 仅 verified 可进沙盒
source: { type: nist_crc_iupac, ref: "…", reviewed_by: "…", reviewed_at: "…" }
applicability: { temp_K: [..], concentration_M: [..], solvent: …, ionic_strength: … }
equilibrium: { Ka: …, Kb: …, Ksp: …, E0: …, deltaG: … }   # 定量，非近似
numerics: { rtol: 1e-8, atol: 1e-10, stiffness: auto, significance: auto }
effects: [ ... ]              # 现象指令，不是渲染代码
```

- 流程：**权威源**（NIST / CRC / IUPAC / 课标附录 / 开放教材）→ **AI 用独立解析解 + ChemPy / Cantera / phreeqpython 交叉对拍** → **用户人工签核** → **黄金用例进 CI**，错了不许进沙盒（台账 4.4 / 10.3）。黄金用例须同时校验 `sane` 与 `success`，并把 PHREEQC 的 `-999` 哨兵值列为非法输入（M0 §4.6 / §5.2）。
- **数值零错红线**：反应方向、产物、计量、守恒、平衡趋势、pH / 浓度数值必须准确；近似只作用于视觉、时间尺度与夸张程度，**不得进入化学事实层**。
- **禁止**整段复制 Open Reaction Database 描述文本（CC-BY-SA 边界），只取事实性反应式与条件，并标注溯源；ORD 数据放独立仓 `data-ord/`。
- 规则改动须在 `golden-cases/` 补断言，并走 `rule_revision`（禁止原地覆盖）。
- i18n：字段名英文 snake_case；物质名 / 术语 / 方程式中英双语（UI 简中默认 + 英文可选，文档仅简体中文）。

### 美术资产贡献要求

- 主调为**出版级写实 2D**；主资产 `tikz-chemlab` 编译输出物（转换链 `lualatex → PDF → pdftocairo -svg → svgo`）；`@itkdm/open-lab-components` 是 HTML fragment 库，**仅作 UI / 缩略图**、不进写实主视图；3D 只做分子 / 晶体 / 球棍模型。
- 只提交**最终产物**（SVG 等），不提交 tikz-chemlab 的 `.sty/.tex` 源码（LPPL 边界，ADR-0004）。
- 每个资产在 `assets/attribution/ASSETS.csv` 登记：源项目、URL、作者、许可证、是否修改、署名文本、用途；bioicons 单图标尤其注意逐项许可。
- 禁止引入许可不明、逐模型授权的商业 3D 资源，或任何商业产品（含 NB）的素材与界面设计。

### 何时需要 ADR

以下改动**必须先提 ADR** 再改代码：

- 修改 `CHARTER.md` 的使命、开发规范或已固定裁决；绕过台账裁决。
- 改变实验台唯一视图、服务端定量求解架构、现象指令协议或 SP-1 调度。
- 引入新的许可证类别、AGPL 依赖、GPL-3.0 组件进主链，或改变主许可证。
- 改变美术资产主调、来源策略、3D 范围、ORD 数据隔离形态。
- 引入新的重组件（数据库 / 消息队列 / 编排器）或改变 Win + Linux 双平台约束。

PR 模板含「是否需要 ADR」勾选项。

## 行为准则

- 简体中文为主，技术术语保留英文原名；事实带**一级来源**，推测标注「判断 / 待 M0 验证」；star 数标快照日期。
- 尊重上游：不破解、不绕授权、不复制商业产品素材与文案。
- 科学准确性声明常驻；本产品不是实验级数据源；危险实验提示「现实操作勿模仿」。
- 遇到不确定的化学事实，宁可留空并标注，不要编造（**数值零错**）。
- 涉及玩法设计须**逐一向需求方确认细节**，不省略、不自行假设。

## 报告问题

- Bug / 事实纠错：GitHub Issues，附来源或复现步骤
- 安全漏洞：见 [SECURITY.md](SECURITY.md)（**不要公开提 issue**）
- 许可证疑虑：提 issue 并标注 `license`，由维护者决定是否需法务确认
