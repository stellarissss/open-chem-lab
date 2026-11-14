# 贡献指南 · CONTRIBUTING

欢迎参与。本项目处于**第一阶段（规划与设计）**结束、即将进入 M0 验证的阶段。贡献前请先读：

1. [CHARTER.md](CHARTER.md) — 固定的目标、开发规范、四项决策（**不可绕过**）
2. [docs/README.md](docs/README.md) — 文档索引
3. [docs/adr/](docs/adr/) — 关键决策及理由
4. [CREDITS.md](CREDITS.md) 与 [NOTICE](NOTICE) — 许可证基线

## 当前最需要的贡献

| 类型 | 说明 |
|---|---|
| 内容精校 | `content/rules/` 的人工精校反应规则（带教材来源、条件、现象、置信度）—— **最高价值** |
| M0 验证 | `docs/10-完整规划与风险登记册.md` 第五节的 10 项验证 |
| 美术资产 | 转换管线、SVG 优化、逐资产署名清单整理 |
| 教材模板 | 各版本教材实验的步骤/评分点（**须自行编写，不复制商业产品文案**） |
| 文档 | 纠正事实、补充来源、翻译 i18n |

## 规范

### 提交

- Conventional Commits：`feat(rule): …` / `fix(sim): …` / `docs: …` / `content: …` / `chore: …`
- 分支：`feat/*`、`fix/*`、`docs/*`、`content/*`
- `main` 受保护，PR 需通过 CI 门禁

### CI 门禁（PR 必过）

- `license-scan`：依赖许可证白名单（MIT/BSD/Apache/ISC/CC0/CC-BY），**GPL/AGPL/LGPL 直接失败**（ADR-0005）
- `schema-validate`：`content/` 全部 YAML/JSON 符合 `schemas/`
- `rule-lint`：计量守恒、条件互斥、置信度闸门、来源完整性
- `golden-cases`：教材代表实验断言（中和、制氧、置换、沉淀、电解…）
- `asset-attribution`：每个入库资产在 `ASSETS.csv` 有记录
- `build`：pnpm build + wasm-pack + Docker 镜像

### 内容（规则）贡献要求

每条规则必须包含：

```yaml
confidence: verified          # 仅 verified 可进实时沙盒
source: { type: textbook, ref: "…", reviewed_by: "…", reviewed_at: "…" }
conditions: { temp_K: [], concentration_M: [], solvent: … }
effects: [ ... ]              # 现象指令，不是渲染代码
```

- **禁止**整段复制 Open Reaction Database 描述文本（CC-BY-SA 边界），只取事实性反应式与条件，并标注溯源。
- **禁止**把未经核实的 ML 猜测规则标为 `verified`。
- 规则改动须在 `golden-cases/` 补断言。

### 美术资产贡献要求

- 只提交**最终产物**（SVG/几何 profile），不提交 tikz-chemlab 的 `.sty/.tex` 源码（LPPL 边界，ADR-0004）。
- 每个资产在 `assets/attribution/ASSETS.csv` 登记：源项目、URL、作者、许可证、是否修改、署名文本、用途。
- CC-BY 资产必须可追溯原始作者（bioicons 单图标尤其注意）。
- 禁止引入许可不明或逐模型授权的商业 3D 资源。

### 何时需要 ADR

以下改动**必须先提 ADR** 再改代码：

- 修改 `CHARTER.md` 的使命、开发规范或四项决策
- 改变四层架构、三级路径或现象指令协议
- 引入新的许可证类别或 GPL/AGPL/LGPL 依赖
- 改变主许可证、美术资产来源策略、3D 器材方案
- 引入新的重组件（数据库/消息队列/编排器）

PR 模板含「是否需要 ADR」勾选项。

## 行为准则

- 简体中文为主，技术术语保留英文原名；事实带来源，推测标注「判断 / 待验证」。
- 尊重上游：不破解、不绕授权、不复制商业产品素材与文案。
- 教学近似声明常驻；不把本产品描述为实验级数据源。
- 遇到不确定的化学事实，宁可留空并标注，不要编造（正确性优先）。

## 报告问题

- Bug / 事实纠错：GitHub Issues，附来源或复现步骤
- 安全漏洞：见 [SECURITY.md](SECURITY.md)（**不要公开提 issue**）
- 许可证疑虑：提 issue 并标注 `license`，由维护者决定是否需法务确认
