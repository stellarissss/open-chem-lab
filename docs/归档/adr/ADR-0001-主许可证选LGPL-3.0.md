# ADR-0001 · 主许可证选 LGPL-3.0

- **状态**：**已接受（v2.0 修订，2026-11-14）**，取代本 ADR 初版「主许可证选 Apache-2.0」
- **决策者**：stellarissss（仓库所有者；台账 A1 主动提出）
- **依据**：[决策台账 §2.6（A1 / 补正 B）](../11-问题与决策台账.md)、§2.8 6.2、§4 C12/C13/C16
- **关联**：`CHARTER` 第 5 条、`LICENSE` / `LICENSE.GPL-3` / `LICENSE.LGPL-3` / `NOTICE`、`CREDITS.md`、`design/07` 合规矩阵、ADR-0005

## 变更史（保留，便于追溯）

| 版本 | 日期 | 决策 | 触发 |
|---|---|---|---|
| v1.0 | 2026-11-14 | **Apache-2.0**（建仓时 `license_template: apache-2.0` 生成） | 初版选型：专利授权、机构法务熟悉、NOTICE 机制容纳致谢 |
| **v2.0** | **2026-11-14** | **LGPL-3.0** | 用户主动裁决 A1：「第四批问题中的合规风险很好解决，把我们的许可证改为 LGPL v3.0 即可」；决策收口后按台账重写 |

> 初版理由（专利授权、企业/学校友好、与宽松组件兼容、NOTICE 容纳署名、不被传染）在事实层面并未失效；换证是**主动选择弱 copyleft 立场**，不是因为初版方案有合规缺陷。

## 背景

需要确定主许可证，使其能容纳大量宽松许可组件、LGPL 求解库（Reaktoro）、CC-BY 资产、CC-BY-SA 数据，以及未来的自托管 / 学校定制 / 潜在商业化。

用户 A1 裁决后，主管依项目规范「法律 / 困难问题先联网查证」，读取 GNU/FSF 官方原文核实（2026-11-14）：

- FSF《Various Licenses and Comments about Them》`https://www.gnu.org/licenses/license-list.html`
- 《GNU LGPL v3.0 正文》`https://www.gnu.org/licenses/lgpl-3.0.html`
- 前轮已核《GNU LGPL v2.1 正文》（Reaktoro LICENSE）

## 【补正 B】核实结论（官方原文要点，不推翻裁决）

| # | 事实 | 依据 |
|---|---|---|
| B1 | **LGPL-3.0 不是独立许可证**：正文开篇「incorporates the terms and conditions of version 3 of the GNU General Public License, supplemented by the additional permissions listed below」——即 **GPLv3 全文 + 附加权限** | LGPL-3.0 引言 |
| B2 | 采用 LGPL-3.0 的产品必须**随附 GPLv3 全文 + LGPL-3.0 全文两份文本**；Combined Works §4 要求「prominent notice that the Library is used」并随附两份许可证 | LGPL-3.0 §4(a)(b) |
| B3 | Apache 的 `NOTICE` 机制不再适配；义务变为「LGPL 显著声明 + 双许可证全文 + 允许逆向调试 + 库可替换（§4(d) 动态链接或提供可重链接材料）」 | LGPL-3.0 §4 |
| B4 | **LGPLv3 ↔ GPLv3 兼容**；**LGPLv2.1 ↔ GPLv2 / GPLv3 兼容** | FSF license-list #LGPLv3 / #LGPLv2.1 |
| B5 | **Apache-2.0 ↔ GPLv3 兼容**；MIT / BSD-3 / ISC 均为 GPL 兼容的宽松许可 | FSF license-list #apache2 / #ModifiedBSD |
| B6 | **AGPLv3 与 GPLv3「technically not compatible in a strict sense」**，仅允许合并独立模块 / 源文件，各自 §13 生效 | FSF license-list #AGPLv3.0 |

**A1 的三项真实影响（决策者须知）**：

1. **裁决成立、可执行** ✅：换 LGPL-3.0 后，Reaktoro(LGPL-2.1)、全部 MIT / BSD / ISC / Apache 依赖仍可并入；§6 / §4 义务由「跨许可证链接」变为「同为 LGPL 家族」，文书与心理上都更顺。
2. **反而解锁了原被隔离的 GPL-3.0 组件**：The Powder Toy、PhET、H5P core 均为 GPL(-3.0)，因 LGPLv3 ↔ GPLv3 兼容（B4），**许可证层面可以链接**。这派生出 C13/C14 新决策点。
3. **换证不是「解决合规风险的必需手段」**：【补正 A】已证明 Apache-2.0 + LGPL-2.1 动态链接本就零风险；A1 的真实价值是「主动选择弱 copyleft + 解锁 GPL-3.0 生态 + 要求衍生回馈」。**AGPL（tptmp）仍严格不兼容，必须继续隔离**（B6）——换证不能解决它。

## 决策

1. **主项目代码采用 LGPL-3.0**。
2. **落地双文本交付**：`LICENSE`（总说明与入口）+ `LICENSE.GPL-3`（GNU GPLv3 全文）+ `LICENSE.LGPL-3`（GNU LGPLv3 全文）。全文取自系统权威副本 `/usr/share/common-licenses/GPL-3`（674 行）与 `LGPL-3`（165 行），避免联网下载超时风险。
3. **`NOTICE` 重写**为 LGPL-3.0 显著声明（§4）+ 双许可证全文引用 + 库可替换 / 逆向调试 / 修改版源码可得说明；不再使用 Apache NOTICE 归因机制。
4. **GPL-3.0 组件（C13/C14）依台账 6.2「不纳入 · 维持现选型」**：换证后许可证层面虽兼容，但**不重做「不重复造轮子」选型**，The Powder Toy / PhET / H5P core 仍只作只读参考或独立页面。理由见下节。
5. **AGPL 与 GPLv2-only 继续严格隔离**；CI `license-scan` 白名单放行 LGPL-2.1 / LGPL-3.0，仍禁止 AGPL / GPLv2-only。
6. **Reaktoro 以动态链接 + 运行时可替换接入**，履行 §6 / §4 义务清单（见 ADR-0005 与 `NOTICE` 第 2 节）。

### 为何换证却不引入 GPL-3.0 组件（台账 §2.8 要求写清，避免被质疑多此一举）

| 维度 | 说明 |
|---|---|
| 换证是**许可证立场** | 弱 copyleft 更契合开源自托管产品；要求衍生回馈；解锁生态**可能性**；让 Reaktoro 与主项目同族，降低文书摩擦 |
| 纳入是**选型决策** | 台账 6.1 已废弃无限画布落沙基座与 Sandspiel；The Powder Toy（落沙）失去立足点；PhET 单 sim 是独立教学设计参考；H5P core 属教学层（已后置长线）。**没有一个 GPL 组件能填补当前架构的真实缺口** |
| 工程成本 | 引入 GPL 组件会带来构建产物边界、§4/§6 义务、独立进程隔离等额外治理成本，与「全局总成本最低」冲突 |
| 结论 | 换证与不引入**不矛盾**：前者定立场，后者定选型。台账 6.2 明确「换证只为立场与解锁可能性，落沙 / 物理仍自研或 MIT 方案」 |

## 理由

1. **主动的弱 copyleft 立场**：比 Apache-2.0 更能保证对主项目的改进回馈，同时不阻止动态链接与自托管定制。
2. **同族简化义务**：Reaktoro(LGPL-2.1) 与 MIT/BSD/ISC/Apache 依赖全部兼容（B4/B5）。
3. **合规交付完整**：B1/B2 决定了必须双文本 + 显著声明，本 ADR 一次性把 `LICENSE` 体系、`NOTICE`、CI 白名单、`CREDITS.md` 同步落地，避免「改了 badge 没改义务」的半吊子换证。
4. **不牺牲能力**：隔离 ≠ 降质。台账 6.2 已确认现有选型覆盖全部关键能力。

## 影响与落地

- `LICENSE` / `LICENSE.GPL-3` / `LICENSE.LGPL-3` / `NOTICE` 四份文件构成完整交付；CI 校验双文本存在且主许可证未回退 Apache-2.0。
- `CHARTER` 第 5 条、`README.md`、`CREDITS.md`、`CONTRIBUTING.md`、`SECURITY.md`、`CHANGELOG.md` 全部同步为 LGPL-3.0。
- ADR-0005 重写为「AGPL / GPLv2-only 隔离 + GPL-3.0 选型不纳入 + LGPL 动态链接 §6 义务 + CC-BY-SA 独立仓」。
- 新增 CI `lgpl-link-check`：动态链接 / 可替换性 / 显著声明 / 许可证全文。
- 合规矩阵（`design/07`）与风险登记册 G 类条目同步。

## 反面约束

- 不得只改 README badge 而不落双文本与 `NOTICE` 显著声明（B1/B2/B3）。
- 不得把 AGPL（tptmp）以「已换 LGPL」为由引入（B6）。
- 不得把 GPL-3.0 组件以「许可证兼容」为由静默纳入主链——须先提 ADR 并重做选型。
- 不得把换证表述为「修复了原有合规漏洞」；Apache-2.0 + 动态链接本就零风险（P4 已修正）。

## 未决 / 复核

- 商业化前法务确认：CC-BY-SA 衍生规则表边界、LPPL 输出物商用、CC-BY 署名充分性、**公开点名对标的比较广告合规**（统一口径 D）。本 ADR 为工程判断，非法律意见。

> **v2.1 注记（2026-11-15，M0 后）**：本 ADR 的**许可证立场与 §6 义务清单不变**。M0 裁决 D2 把 Reaktoro 改为**独立微服务**（`reaktoro-service`，conda 镜像，UDS/protobuf 通讯），「动态链接 + 运行时可替换 + 显著声明 + 允许逆向调试」仍在服务镜像内逐项履行；**进程隔离不免除义务**。技术选型以 [`ADR-0009`](ADR-0009-M0实测驱动的选型调整.md) 与台账 §9 为准；本 ADR 的变更史与裁决理由不作改写。
