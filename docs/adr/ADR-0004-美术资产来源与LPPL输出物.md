# ADR-0004 · 美术资产来源与 LPPL 输出物策略

- **状态**：已接受（2026-11-14）
- **关联**：`CHARTER` 第 4 条、`CREDITS.md`、`research/03`、`design/04`

## 背景

用户指定美术资产须来自开源项目，点名 `tikz-chemlab`（LaTeX 宏包，需转换）与 `@itkdm/open-lab-components`（React/HTML 组件），并授权「找更好的」。

核实结果（2026-11-14）：

| 项目 | 真实情况 |
|---|---|
| `aihua/tikz-chemlab` | v1.0.0，CTAN 收录，**LPPL-1.3c**，13 个参数化器材宏，是 `pst-labo` v2.07 的 TikZ 移植（原作者 Denis Girou / Christophe Jorssen / Manuel Luque / Herbert Voß）。GitHub API 显示「无许可证」是因为没有单独 LICENSE 文件，**CTAN 与 README 均明确 LPPL-1.3c** |
| `@itkdm/open-lab-components` | MIT，★10，npm v0.1.1，**213+ 组件 / 41 分类**，其中化学相关 **37 个**（26 器材 + 5 交互反应 + 3 模型 + 气体 + 溶液）。零依赖 HTML fragment + JS API + Registry + MCP Server |

**LPPL 1.3c 条款原文核实**（latex-project.org）：
- Clause 1：`Activities other than distribution and/or modification of the Work are not covered by this license; they are outside its scope. In particular, the act of running the Work is not restricted and no requirements are made concerning any offers of support for the Work.`
- Clause 6（修改源码再分发）：需明确标识修改版、附变更日志、不暗示原作者支持、附完整未修改原件或获取信息。
- Clause 9：以其他格式分发 Work 不解除义务 —— 提醒「把 `.tex` 整体翻译成 JS 组件再分发」仍受约束。

## 决策

### 1. 来源组合（不重复造轮子，全部复用）

| 需求 | 来源 |
|---|---|
| 常规器材（可动态） | `@itkdm/open-lab-components` 26 件 `chemistry/labware`（薄 React 包装，不改写 213 个 fragment） |
| 组合装置（滴定/蒸馏/回流，出版级） | `tikz-chemlab` 13 宏 → **编译输出物转 SVG** |
| 结构式/分子 3D | SmilesDrawer / Kekule.js / RDKit.js / 3Dmol.js（运行时生成，不做静态资产） |
| UI 图标 | Lucide (ISC) / Tabler (MIT) |
| 高阶仪器插画 | LabIcons (CC-BY-4.0，署名 Manon Zuurmond) |
| 科学图标 | bioicons（**逐个核验单图标许可**） |
| 音效/粒子贴图 | Kenney (CC0，待 M0 复核包内 LICENSE) |
| **3D 器材** | **Three.js 程序化建模**（见 ADR-0007） |

### 2. LPPL 输出物策略（关键）

```
构建期：从 CTAN 拉取源码 → standalone 编译 → dvisvgm/pdf2svg → SVG
   → 只有 SVG 产物进 assets/，宏包源码不入库、不随产品分发
仓库内：只保留生成脚本 + 器材参数表 + SVG 产物 + 署名
```

- **依据 Clause 1**：编译输出物是「运行 Work 的结果」，不是 Work 或 Derived Work，可用于本产品（Apache-2.0 主项目），不受 LPPL 分发条款约束。
- **不 fork、不修改、不分发宏包源码**。若未来确需改宏包，按 Clause 6 改名 + 变更日志 + 附原始副本，且放在独立 `upstream/` 目录，与主产品代码隔离。
- 在 `CREDITS.md` 与 `ASSETS.csv` 署名 aihua + pst-labo 四位原作者，注明 LPPL-1.3c（输出物）。

### 3. 运行期动态化

tikz-chemlab 的「参数化」保留在**构建期**（批量生成不同液位/倾斜/塞子的 SVG 变体）；运行期液位/颜色/倾斜用 `clipPath` + CSS 变量 + `transform` 驱动，避免资产数量爆炸。

## 理由

1. **合规**：只碰输出物，绕开 LPPL 最严苛的修改分发条款，同时仍完整致谢上游。
2. **质量**：tikz-chemlab 出版级线条 + 组合装置，open-lab-components 可直接挂载、CSS 变量可动态改 —— 二者互补而非替代。
3. **不重复造轮子**：26 件器材、5 个交互反应组件、13 个装置宏全部现成；自研只写约 30 行包装层与转换脚本。
4. **可扩展**：器材参数表是单一事实源，同时驱动 2D SVG、3D 几何、容量与物理约束。

## 影响

- `design/04` 给出完整转换命令、目录、动态化方案与逐资产署名清单。
- `tools/asset-pipeline/` 在 M0 落地；`assets/attribution/ASSETS.csv` 为 CI 校验依据。
- 仓库内**禁止**出现 tikz-chemlab 的 `.sty/.tex` 源文件。

## 待 M0 验证 / 未决

1. `dvisvgm --pdf` vs `pdf2svg` 对 TikZ 渐变/图案的保真度（择优）。
2. 液体层能否拆出；若不可，用 `clipPath` 遮罩兜底。
3. open-lab-components 26 件器材视觉质量与 StrictMode 双挂载。
4. Kenney 资产包内 LICENSE 是否确为 CC0 1.0。
5. **法务确认（商业化前）**：LPPL 输出物商用边界 —— 本 ADR 是工程判断，非法律意见。
