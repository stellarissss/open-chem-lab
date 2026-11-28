# 贡献指南 · CONTRIBUTING

欢迎参与。本项目为**单人 + AI Agent** 体制，开源非盈利、娱乐性质，贡献者协议从简，不设复杂协作机制。遵循**文档驱动 + 敏捷轻量**流程（当前进度见 [docs/02-Roadmap.md](docs/02-Roadmap.md)）。

## 先读这些

0. [AGENTS.md](AGENTS.md) — AI/开发者第一站（现场指针、当前焦点、硬约束）
1. [docs/02-Roadmap.md](docs/02-Roadmap.md) — 当前进度、里程碑、薄切片清单
2. [docs/01-Architecture.md](docs/01-Architecture.md) — 唯一技术与产品真理源（**不可绕过**）
3. [docs/03-DocDD-Process.md](docs/03-DocDD-Process.md) — 开发流程与 spec 写法
4. [docs/specs/](docs/specs/) — 当前切片规格
5. [CREDITS.md](CREDITS.md) / [NOTICE](NOTICE) — 许可证基线与 LGPL 显著声明

## 当前最需要的贡献

| 类型 | 说明 |
|---|---|
| **真实反应内容精校** | `content/rules/` 中已验算的真实反应参数（Ka/Kb/Ksp/E°/ΔG、热物性、动力学），带权威源 + 适用条件 + AI 对拍记录 + 人工签核 —— **最高价值** |
| 美术资产 | tikz-chemlab 编译输出物 → SVG 转译、写实风格统一、逐资产署名整理 |
| 内容体系整理 | 按化学体系 / 玩法 / 器材组织反应覆盖；课标 / 教材为可选检索标签，不是内置教学功能 |
| 文档与代码 | 纠正事实、补一级来源、按 03 流程推进切片 |

## 规范

### 提交

- Conventional Commits：`feat(rule): …` / `fix(solver): …` / `docs: …` / `content: …` / `chore: …`
- 分支：`feat/*`、`fix/*`、`docs/*`、`content/*`；`main` 受保护，PR 需通过 CI。
- **禁止**提交任何密钥、token、`.env` 或受限数据原始数据文件。

### 验证与门禁（敏捷轻量，见 03）

- 不在每个任务收尾强制跑全套 CI；以「诚实计算红线 + 最小充分证据 + 用户随时可打断」保障质量，验证结果由测试产物与 git log 承载。
- 产品级强制门禁已接入 CI：构建（`build`/`typecheck`）、`schema-validate`、`asset-attribution`、`content-consistency`（可取药品全部可玩）、物化幂等、`golden-cases`（工程质量对拍）、`evidence-check`、`report`（过渡期，随台面快照改造替换）、`doc-hygiene-check`、`license-scan`、部署可达 `e2e`（完整清单见 `docs/01-Architecture.md` §7.2）；`lgpl-link-check`、`rule-lint`、`dual-platform` 随相关切片接入。

### 内容（真实反应）贡献要求

**严格只做真实库**：不接受虚构物质、用户自制物质、自定义规则、MOD 或规则包工坊。每条参数必须包含：

字段以 `schemas/*.v1.schema.json` 为准，照抄 `content/rules/neutralization/` 里的真实卡即可，不要另造字段名。护栏要点（真实字段名）：

```yaml
confidence: { level: verified, note: "…" }   # 仅 verified 可进可玩层
source: { kind: authoritative_db, ref: "…", snapshot_date: "…", sha256: "…" }
review: { status: signed_off, reviewer: "…", date: "…" }
applicability: { conditions: [...], temp_range_K: [...] }
rule_revision: 1                              # 参数改动递增，禁原地覆盖
equilibrium: { log_k_25C: …, delta_h: "…" }   # 定量，回指权威源 .dat
effects: [ ... ]                              # 现象指令 ID，不是渲染代码
```

完整样例见 `content/rules/neutralization/compounds/hcl.json` 与 `content/rules/neutralization/rules/strong_acid_strong_base.json`。

流程：**权威源 → AI 用独立解析解 + chempy/Cantera/phreeqpython 交叉对拍 → 用户人工签核 → 黄金用例进 CI**，错了不许进沙盒。黄金用例须同时校验 `sane` 与 `success`，PHREEQC `-999` 哨兵值列为非法输入。**诚实计算**：一切数值来自实时求解引擎，不虚构、不硬编码、来源锚定；黄金用例承担数值正确性回归（数值错误属常规 bug，发现即修），禁止以预设数值冒充计算结果。参数改动走 `rule_revision`（禁止原地覆盖）并补黄金用例。字段名英文 snake_case；物质名/术语/方程式双语（文档仅简体中文）。详见 `01-Architecture.md` 第五节。

### 美术资产贡献要求

- 主调为**出版级写实 2D**；主资产 tikz-chemlab 编译输出物（转换链 `lualatex → PDF → pdftocairo -svg → svgo`）；`open-lab-components` 仅作 UI/缩略图；3D 只做分子/晶体/球棍模型。
- 只提交**最终产物**（SVG 等），不提交 tikz-chemlab 的 `.sty/.tex` 源码（LPPL 边界）。
- 每个资产在 `assets/attribution/ASSETS.csv` 登记源项目、URL、作者、许可证、是否修改、署名文本、用途。
- 禁止引入许可不明的商业资源，或任何商业产品（含 NB）的素材与界面设计。

### 何时需要确认重大变更

以下改动须先说明动机与影响、与用户确认并同步 `01-Architecture.md`：产品定义或使命、技术栈基线、许可证基线、里程碑验收口径、实验台唯一视图/服务端求解架构/现象协议/调度、ORD 数据隔离形态、引入重组件或改变双平台约束。

## 行为准则

- 简体中文为主，技术术语保留英文；事实带**一级来源**，推测标注「判断」；star 数标快照日期。
- 尊重上游：不破解、不绕授权、不复制商业产品素材与文案。
- 科学准确性声明常驻；本产品不是实验级数据源；危险实验提示「现实操作勿模仿」。
- 遇到不确定的化学事实，宁可留空并标注，不要编造（**诚实计算**）。
- 涉及玩法设计须**逐一向需求方确认细节**，不省略、不自行假设。

## 报告问题

- Bug / 事实纠错：GitHub Issues，附来源或复现步骤
- 安全漏洞：见 [SECURITY.md](SECURITY.md)（**不要公开提 issue**）
- 许可证疑虑：提 issue 并标注 `license`，由维护者决定是否需法务确认
