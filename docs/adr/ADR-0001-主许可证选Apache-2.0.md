# ADR-0001 · 主许可证选 Apache-2.0

- **状态**：已接受（2026-11-14，建仓时确立）
- **决策者**：stellarissss（仓库所有者）
- **关联**：`CHARTER` 第 5 条、`CREDITS.md`、`design/07` 合规矩阵

## 背景

需要为新建仓库选定主许可证，且必须能容纳大量宽松许可第三方组件、CC-BY 资产、CC-BY-SA 数据，以及未来可能的商业化/学校部署。

## 备选

| 许可证 | 优点 | 缺点 |
|---|---|---|
| MIT | 最简、最宽松 | 无明确专利授权；无贡献者许可条款 |
| **Apache-2.0** | 明确专利授权、专利报复条款、贡献者许可、NOTICE 机制、企业/学校法务熟悉 | 文本较长，需维护 NOTICE |
| GPL-3.0 / AGPL-3.0 | 强制衍生开源 | 与「可闭源二次开发 + 学校自托管定制」冲突；且会与打算隔离的 GPL 组件混淆 |
| MPL-2.0 | 文件级弱 copyleft | 与大量 MIT/BSD 组件混用时边界管理复杂 |

## 决策

**主代码采用 Apache-2.0**（建仓时通过 `license_template: apache-2.0` 生成 `LICENSE`）。

## 理由

1. **专利授权**：化学仿真涉及算法与引擎，Apache-2.0 第 3 条提供明确专利许可，MIT 没有。
2. **企业/学校友好**：对标 NB 的落地场景是学校，Apache-2.0 是机构法务最熟悉的宽松许可。
3. **与组件链兼容**：MIT / BSD-3 / ISC 组件均可并入 Apache-2.0 项目（保留各自声明即可）。
4. **NOTICE 机制天然容纳致谢**：`CREDITS.md` + `NOTICE` 正好承载 RDKit、3Dmol.js、LabIcons、tikz-chemlab、bioicons 等署名义务。
5. **不被传染**：与 GPL/AGPL 组件物理隔离后，主产品可保持 Apache-2.0（见 ADR-0005）。

## 影响与落地

- 新增 `NOTICE` 文件（M1 前），汇总第三方版权声明与论文引用（3Dmol.js Bioinformatics 论文）。
- `CREDITS.md` 作为人类可读致谢；`assets/attribution/ASSETS.csv` 作为资产级署名。
- `data-ord/` 独立仓保留 CC-BY-SA-4.0；衍生规则表单独署名并保留 SA 声明。
- CI `license-scan` 白名单：MIT / BSD / Apache-2.0 / ISC / CC0 / CC-BY；禁止 GPL/AGPL/LGPL 进主构建产物。

## 未决 / 复核

- 商业化前由法务确认「CC-BY-SA 衍生规则表」与「LPPL 输出物」边界（工程判断，非法律意见）。
