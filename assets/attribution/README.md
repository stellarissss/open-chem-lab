# 逐资产署名清单 · Asset Attribution

本目录维护**每一个入库美术资产**的许可与署名记录，是合规硬要求（ADR-0004 / ADR-0005、`design/04`）。
**《ST实验室》主视觉为出版级写实 2D**（台账 5.3 / 6.3）：tikz-chemlab 编译输出物为**唯一主资产**；`@itkdm/open-lab-components` 是 HTML fragment 库（非 React），依 **D8 仅作 UI 元素与缩略图**、不进实验台写实主视图；3D 只做分子 / 晶体 / 球棍模型。卡通风格资产不与写实主调混用。

## 文件

| 文件 | 用途 |
|---|---|
| `ASSETS.csv` | 主清单，每个资产一行（M0 起随资产入库逐条填充） |
| `LICENSES/` | 各上游许可证全文副本（LPPL-1.3c、CC-BY-4.0、CC-BY-3.0、CC-BY-SA-4.0、MIT、ISC、BSD-3-Clause、CC0-1.0） |

## CSV 字段（固定，CI 校验）

```csv
asset_id,source_project,source_url,author,license,modified,attribution_text,used_in
```

| 字段 | 说明 |
|---|---|
| `asset_id` | 仓库内资产文件标识（如 `tkz_Titration`、`olc_beaker`） |
| `source_project` | 上游项目名（含衍生链，如 `tikz-chemlab + pst-labo`） |
| `source_url` | 上游仓库 / CTAN / npm 页面 |
| `author` | 作者 / 机构；多作者用 `;` 分隔 |
| `license` | SPDX 或明确名称（如 `LPPL-1.3c (generated output only)`） |
| `modified` | `yes` / `no`；CC-BY 要求声明改动 |
| `attribution_text` | 可直接放进 About 页 / 图注的署名文本 |
| `used_in` | 产品中使用位置 |

## 示例记录（格式示范，实际以入库资产为准）

```csv
asset_id,source_project,source_url,author,license,modified,attribution_text,used_in
tkz_Titration,aihua/tikz-chemlab + pst-labo,https://ctan.org/pkg/tikz-chemlab,Aihua Wang; D.Girou; C.Jorssen; M.Luque; H.Voss,LPPL-1.3c (generated output only),yes,Generated from tikz-chemlab v1.0.0 (LPPL-1.3c); original pst-labo by D.Girou et al.,apparatus/titration
olc_beaker,itkdm/open-lab-components,https://github.com/itkdm/open-lab-components,itkdm,MIT,no,(c) itkdm - MIT,ui/thumbnail
labicon_massspec,CPM/LabIcons,https://github.com/Center-for-Proteomics-and-Metabolomics/LabIcons,Manon Zuurmond (CPM),CC-BY-4.0,yes,"Selected graphical elements ... were designed by Manon Zuurmond and are used under a CC BY license.",illustrations
bioicon_flask,duerrsimon/bioicons (Servier),https://smart.servier.com/,Servier,CC-BY-3.0,no,flask icon by Servier - CC BY 3.0,icons
```

## 硬性规则

1. **tikz-chemlab / pst-labo**：必须同时署名 Aihua Wang 与 pst-labo 四位原作者；注明「**仅使用编译输出物**」，宏包源码不入库、不随产品分发（LPPL 1.3c Clause 1 运行不受限制、Clause 6 修改分发才受约束）。
2. **bioicons**：平台 MIT **不等于**每个图标 MIT。必须逐个记录原始作者与许可（Servier CC-BY 3.0、DBCLS / TogoTV 等），不得整包当作 MIT。
3. **LabIcons / BioArt**：CC-BY-4.0，About 页 + 图注可见，注明改动。
4. **Kenney**：**F3 已销项，CC0 1.0**（官网 particle-pack 页标注 + 包内 `LICENSE.txt` 原文 + CC0 1.0 官方法典三级核实，见 `04-M0验证报告` §5.6），可入库、可商用、署名非强制；**只取通用音效与粒子贴图，卡通 2D/3D 器材不入库**（与写实主调冲突）。官网签名下载端点 403（会话/校验），包内 LICENSE 经公开第三方镜像转录核对。
5. **open-lab-components**：`used_in` 必须为 `ui/thumbnail`；出现 `apparatus/*` 即视为违反 D8（该库简笔示意风与写实主调冲突）。
6. **3Dmol.js**：BSD-3 声明（M0 已销项 F2）+ Bioinformatics 论文引用 DOI `10.1093/bioinformatics/btu829` 写进 About 页（本清单也记一条）。
7. **ORD 衍生规则**：CC-BY-SA-4.0 溯源标记，数据放**独立公开仓 `data-ord/`**（主仓仅 submodule 引用）；不属美术资产，但同样受 CI 检查。
8. **禁止入库**：许可不明、逐模型授权、AGPL / GPLv2-only 素材、卡通风格器材（与写实主调冲突）、任何商业产品（含 NB）的素材与界面设计。
9. **star 数**：文档引用上游指标须标快照日期（阶段一 `2026-11-14`、阶段二 M0 `2026-11-15`）。

## CI

`asset-attribution` 检查：`assets/` 下每个资产文件都在 `ASSETS.csv` 有对应记录，且 `license` 字段在白名单内；同时检查仓库内不含 tikz-chemlab 宏包源码。缺失即失败。
