# ADR-0005 · 不链接 GPL/AGPL 组件，CC-BY-SA 数据隔离

- **状态**：已接受（2026-11-14）
- **关联**：`CHARTER` 第 5 条、`CREDITS.md`、`design/07` 合规矩阵、ADR-0001

## 背景

主项目为 **Apache-2.0**（可闭源二次开发、可商用、学校可定制）。调研发现两类会「传染」或附加义务的资源：

### 强 copyleft 组件

| 项目 | 许可 | star | 用途诱惑 |
|---|---|---|---|
| The Powder Toy | **GPL-3.0** | 5,409 | 反应矩阵、热/压/电耦合、Lua 自定义元素、社区存档工坊，最像我们要做的沙盒 |
| tptmp | **AGPL-3.0** | — | 多人同步现成实现 |
| PhET sims | **GPL** | — | 化学小仿真教学设计，官方明确「定制现有 sim 须遵守 GPL」 |
| H5P core | **GPL-3.0** | 155 | 教学内容组织 |
| cdk / Jmol-SwingJS | LGPL-2.1 | 614 / 63 | Java/JS 化学工具库 |

### 带 SA 义务的数据

`open-reaction-database/ord-data`：**数据 CC-BY-SA-4.0**（仓库 README 明确双许可：数据 CC-BY-SA-4.0 / `scripts/` 代码 Apache-2.0）。以其为源生成的规则表可能带「相同方式共享」义务。

## 决策

### 1. GPL/AGPL/LGPL 组件：物理隔离，只读参考

- **不 import、不链接、不合并构建产物、不移植源码进主仓**。
- 允许的方式：① 只读源码/文档获取设计思路；② 作为**独立自托管页面**原样运行（PhET 单 HTML、H5P 独立进程），与主产品不共享进程与构建产物。
- 多人协作功能**自研**（Yjs，MIT），不碰 tptmp 的 AGPL。
- 落沙引擎用 **Sandspiel (MIT)** 而非 The Powder Toy，从根上避开 GPL。
- LGPL 组件（CDK、Jmol）只作参考；若确需，仅动态链接 + 可替换形态，且单独 ADR + 法务确认。

### 2. CC-BY-SA 数据：分仓 + 署名 + 只取事实

- `data-ord/` 为**独立 Git 仓库 / submodule**，与主代码仓物理分离；保留 CC-BY-SA-4.0 声明与署名。
- 由 ORD 抽取生成的规则表**单独标注 CC-BY-SA-4.0 溯源**，与自有 `content/rules/`（Apache-2.0）分目录。
- **只抽取事实性反应式与条件**（反应物、产物、条件、计量），不整段复制 ORD 的描述文本、产率叙述或数据集表述 —— 事实不受版权保护，表达才受，且降低 SA 传染面。
- 抽取规则一律 `confidence: extracted`，人工复核后才升 `verified` 进沙盒（同时满足 ADR-0002 正确性要求）。
- 产品 About 页与 `CREDITS.md` 保留 ORD 署名与 SA 声明链接。

### 3. 其他署名义务（一并纳入）

| 对象 | 义务 |
|---|---|
| LabIcons (CC-BY-4.0) | 署名 Manon Zuurmond、注明改动 |
| bioicons 单图标 | 逐个引用作者与许可（CC0/MIT/CC-BY 混合） |
| 3Dmol.js (BSD-3) | 版权声明 + 引用 Bioinformatics 论文 |
| RDKit (BSD-3) | 版权声明 |
| PubChem | 引用来源、≤ 5 req/s |

### 4. CI 强制

`license-scan` 每次 PR 扫描 `pnpm-lock.yaml` / `Cargo.lock` / `requirements.lock`，白名单（MIT/BSD/Apache/ISC/CC0/CC-BY）外直接失败；检测到 GPL/AGPL/LGPL 依赖立即失败并提示本 ADR。同时校验 `assets/attribution/ASSETS.csv` 覆盖全部入库资产。

## 理由

1. **保住 Apache-2.0 的价值**：一旦链接 GPL，整个产品须开源，与「可闭源二次开发/学校定制/未来商业化」冲突。
2. **AGPL 更危险**：网络使用即视为分发，连「独立服务」都可能触发，必须完全不碰。
3. **数据 SA 边界可控**：分仓 + 只取事实 + 独立署名，把义务限制在数据衍生品，不污染主代码。
4. **不牺牲能力**：Sandspiel(MIT) + Yjs(MIT) + RDKit(BSD) + ltijs(Apache) 已覆盖被隔离组件的全部关键能力 —— **隔离不等于降质**。

## 影响

- `design/05` 依赖方向规则与 CI 门禁；`design/07` 合规矩阵。
- `research/02` B/C 组清单标注「仅参考」。
- 仓库 PR 模板强制勾选「是否引入新依赖 / 是否需 ADR」。

## 未决 / 复核

- 商业化前法务确认：① ORD 衍生规则表的 SA 边界；② PhET 独立页面自托管的具体合规形态。
- CC-BY 资产署名充分性（About 页 + 图注 + CSV 三处覆盖）。
