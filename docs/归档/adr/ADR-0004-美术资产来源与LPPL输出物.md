# ADR-0004 · 美术资产来源与 LPPL 输出物策略（出版级写实）

- **状态**：**已接受（v2.0 修订，2026-11-14）**
- **决策者**：stellarissss（台账 5.3 / 6.3；原始资产规范由用户指定）
- **依据**：台账 5.3（C19）、6.3、§7.4 F3；用户第 3 条消息「美术资产来源必须开源」
- **关联**：`CHARTER` 第 4 条、`CREDITS.md`、`research/03`、`design/04`、`assets/attribution/`、`tools/asset-pipeline/`

## 变更史

| 版本 | 决策 | v2.0 调整 |
|---|---|---|
| v1.0 | tikz-chemlab（组合装置）+ open-lab-components（常规器材）**互补并列**；双层皮肤可切换；Three.js 程序化 3D 器材 | 台账 5.3 定主调**出版级写实**、推翻双层皮肤；6.3 定 **2D 写实为主、3D 只做分子**；tikz-chemlab **升为主资产**，open-lab-components **降为辅**；程序化 3D 器材降级长线 |

## 背景

用户指定美术资产须来自开源项目，点名 `tikz-chemlab`（LaTeX 宏包，需转换）与 `@itkdm/open-lab-components`（**M0 核实为 HTML fragment 库，非 React**），并授权「找更好的」。

核实结果（2026-11-14）：

| 项目 | 真实情况 |
|---|---|
| `aihua/tikz-chemlab` | v1.0.0，CTAN 收录，**LPPL-1.3c**，13 个参数化器材宏，是 `pst-labo` v2.07 的 TikZ 移植（原作者 Denis Girou / Christophe Jorssen / Manuel Luque / Herbert Voß）。GitHub API 显示「无许可证」是因无单独 LICENSE 文件，**CTAN 与 README 均明确 LPPL-1.3c** |
| `@itkdm/open-lab-components` | MIT，★10（快照），npm v0.1.1，**210 组件 / 化学相关 35 个**。M0 实测：零依赖 **HTML fragment 库**（`index.js` 提供 `list/get/readSync/load`），SVG + 14 个 `--cmp-*` CSS 变量，简笔示意风无渐变 / 高光 |

**LPPL 1.3c 条款原文核实**（latex-project.org）：

- **Clause 1**：`Activities other than distribution and/or modification of the Work are not covered by this license... In particular, the act of running the Work is not restricted and no requirements are made concerning any offers of support for the Work.`
- **Clause 6**（修改源码再分发）：需明确标识修改版、附变更日志、不暗示原作者支持、附完整未修改原件或获取信息。
- **Clause 9**：以其他格式分发 Work 不解除义务 —— 提醒「把 `.tex` 整体翻译成 JS 组件再分发」仍受约束。

## 决策

### 1. 主调与来源组合（v2.0）

**主调：出版级写实 2D**（台账 5.3）。废弃「双层皮肤可切换」「卡通游戏化主视图」「Kenney 卡通器材」。

| 需求 | 来源 | 角色 |
|---|---|---|
| 写实器材与组合装置（滴定 / 蒸馏 / 回流，出版级线条） | **`tikz-chemlab` 13 宏 → 编译输出物转 SVG** | **主资产** |
| UI 元素 / 缩略图 | `@itkdm/open-lab-components` 化学相关组件（CSS 变量注入或 Web Component 封装） | **仅 UI / 缩略图（D8）**，不进实验台写实主视图 |
| 结构式 / 分子 3D | SmilesDrawer / Kekule.js / RDKit.js / **3Dmol.js**（运行时生成，不做静态资产） | 运行时 |
| UI 图标 | Lucide (ISC) / Tabler (MIT) | — |
| 高阶仪器插画 | LabIcons (CC-BY-4.0，署名 Manon Zuurmond) | 需署名 |
| 科学图标 | bioicons（**逐个核验单图标许可**） | 需逐项署名 |
| 音效 / 粒子贴图 | Kenney (CC0，待 M0 复核包内 LICENSE)；**卡通 2D/3D 器材不入库** | 需复核 |
| **3D** | **只做分子 / 晶体 / 球棍模型（3Dmol.js）**；程序化 3D 器材（Three.js `LatheGeometry`）**降级为可选长线、不进 M1** | 见 ADR-0007 |

### 2. LPPL 输出物策略（关键，不变）

```
构建期：从 CTAN 拉取源码 → `lualatex` 编译为 PDF → `pdftocairo -svg` → `svgo` → SVG
（M0 实测：DVI→dvisvgm 与 `dvisvgm --pdf` 双路径均失败，此链为唯一可行路径，D5）
   → 只有 SVG 产物进 assets/，宏包源码不入库、不随产品分发
仓库内：只保留生成脚本 + 器材参数表 + SVG 产物 + 署名
```

- **依据 Clause 1**：编译输出物是「运行 Work 的结果」，不是 Work 或 Derived Work，可用于本产品（**LGPL-3.0** 主项目），不受 LPPL 分发条款约束。
- **不 fork、不修改、不分发宏包源码**。若未来确需改宏包，按 Clause 6 改名 + 变更日志 + 附原始副本，且放在独立 `upstream/` 目录，与主产品代码隔离，并新增 ADR。
- 在 `CREDITS.md` 与 `ASSETS.csv` 署名 aihua + pst-labo 四位原作者，注明 LPPL-1.3c（输出物）与「仅使用编译输出物」。
- CI 强制检查仓库内不含 `tikz-chemlab.sty` / `.tex` / `Obj.tex`。

### 3. 运行期动态化

tikz-chemlab 的「参数化」保留在**构建期**（批量生成不同液位 / 倾斜 / 塞子的 SVG 变体）；运行期液位 / 颜色 / 倾斜用 `clipPath` + CSS 变量 + `transform` 驱动，避免资产数量爆炸。`apparatus` 参数表是单一事实源，同时驱动 SVG 渲染、容器容量与物理约束。

### 4. 跨平台

转换脚本须在 **Windows（WSL2 / Docker Desktop）与 Linux** 均可跑；路径统一小写、文本 LF（`.gitattributes`）。

## 理由

1. **合规**：只碰输出物，绕开 LPPL 最严苛的修改分发条款，同时仍完整致谢上游。
2. **质量**：tikz-chemlab 出版级线条 + 组合装置，正好支撑「一切按实验室规格」的实验台范式（5.1）。
3. **不重复造轮子**：26 件器材、5 个交互反应组件、13 个装置宏全部现成；自研只写约 30 行包装层与转换脚本。
4. **收敛后更省**：3D 收敛到分子级后，不再需要批量器材 GLB 与轮廓提取管线，全局总成本更低（6.3）。

## 影响

- `design/04` 给出完整转换命令、目录、动态化方案与逐资产署名清单；`tools/asset-pipeline/README.md` 删除 `extract-profile.mjs` 主流程。
- `assets/attribution/ASSETS.csv` 为 CI 校验依据；白名单排除 AGPL / GPLv2-only 素材与卡通器材。
- `CREDITS.md` 把 tikz-chemlab 升为主资产、open-lab-components 降为辅。
- 仓库内**禁止**出现 tikz-chemlab 的 `.sty` / `.tex` 源文件。

## 待 M0 验证 / 未决

1. ~~`dvisvgm --pdf` vs `pdf2svg` 保真度择优~~ → **M0 已实测销项**：改用 `pdftocairo -svg`，产物纯路径、零字体依赖、21 clipPath、液位可控（D5）。
2. 液体层能否拆出；若不可，用 `clipPath` 遮罩兜底。
3. ~~open-lab-components 写实主调兼容性、StrictMode 双挂载~~ → **M0 已实测销项**：非 React、简笔示意风与写实主调冲突，D8 限定仅 UI / 缩略图；StrictMode 验收项作废。
4. Kenney 资产包内 LICENSE 是否确为 CC0 1.0（仅取通用音效 / 粒子贴图）。
5. **法务确认（商业化前）**：LPPL 输出物商用边界 —— 本 ADR 是工程判断，非法律意见。
