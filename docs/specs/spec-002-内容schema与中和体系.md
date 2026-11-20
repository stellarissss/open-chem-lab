# spec-002 · 内容 schema 与中和体系样例

> **状态：粗稿**（由切片 001 回写时预铺）。本稿只定方向与边界，细节留白；开工时在本文件就地补全为正式规格，不另建副本。

## 目标

建立「可玩物质库 + 静态参数物化层」的最小真实数据与契约，以**酸碱中和体系**为首个样例，把 `01-Architecture.md` 第五节的数据模型从设计落到仓库——让后续求解切片有可加载、可校验、零错签核的事实层输入。

## 范围（大略）

**做**：
- 在 `schemas/` 补齐核心实体的 JSON Schema：`compound` / `apparatus` / `reaction_rule` / `solution_speciation`，并由 `@st/protocol` 的 `build:types` 生成 TS 类型（延续切片 001 的契约先行机制）。
- 在 `content/rules/` 以**酸碱中和**落一组最小真实数据：可玩物质卡 + 条件化反应规则，覆盖 fact / presentation / safety 三层。
- 落地事实层的护栏字段与门禁：`source` / `confidence` / `review`、`applicability`、`data_class`、`rule_revision`；非 verified 不进可玩层、`ml_guess` 禁用。
- 构建期物化链与黄金用例雏形（`content/golden-cases/`）：数据可机读、可 diff、可回滚；运行时零网络依赖。

**不做**（明确边界）：
- 任何求解逻辑（→ spec-003 单体系求解）。
- 物种面板、时间轴、WASM 现象、实验报告、装置搭建交互（→ spec-004~006）。
- 反应规模扩张；本切片只做中和这一个体系的样例，不铺开多体系（规模属 M2）。
- 虚构物质、自制规则、MOD 工坊；未经签核的数值不进事实层。

## 验收标准（大略，可判定）

1. `schemas/` 新增核心实体 schema，TS 类型生成成功，`pnpm build` 通过；各语言侧可引用同一事实源。
2. 中和体系样例数据通过 schema 校验；字段完整（source/confidence/applicability 必填），非 verified 不进可玩层。
3. 数据经权威源 + AI 对拍 + 用户签核 + 黄金用例才进事实层；计量守恒、条件互斥经核对，数值零错。
4. 物化层构建期固化、运行时零网络依赖；参数变更走 `rule_revision`、可回滚。
5. 如实记录做了哪些验证、哪些受限（见 `03-DocDD-Process.md` 第四节）。

## 技术要点

遵循 `01-Architecture.md`：
- 数据模型（第五节）：`compound` / `apparatus` / `reaction_rule` / `solution_speciation` 字段定义；三类数据分层（fact 零错 / presentation 可夸张标来源 / safety 严谨）；正确性护栏（计量守恒、条件互斥、置信度闸门、来源/对拍/签核完整性、`applicability` 必填、ORD 衍生带 CC-BY-SA 溯源）。
- 权威数据供应链（第五节 5.2）：构建期离线固化 → 候选池 → AI 对拍 → 用户签核 → 黄金用例 → 静态参数层；快照记录 `endpoint / license / snapshot_date / sha256`。
- 工程结构（第六节）：`schemas/` 单一事实源、`content/rules/` 按体系分目录、`content/golden-cases/`、`content/ai-crosscheck/`。
- 红线（第七节）：事实零错、真实库无工坊、CC-BY-SA 数据独立仓、LPPL 只取编译输出物。

**复用优先**：schema 校验与类型生成沿用切片 001 已建立的 `json-schema-to-typescript` 链；化学参数从权威源取，不自造。

## 任务拆解

> 粗稿阶段留白——开工时补齐为有序步骤。

## 待开工时确认的方向

> 以下细节**刻意不在粗稿锁定**，开工时逐一向用户确认后再定，避免预支未裁决内容：
> - 中和体系的具体物质清单与边界（强酸强碱 / 是否含弱酸弱碱 / 指示剂）。
> - 首批物质与反应的数量、优先级。
> - 具体热力学/平衡常数数值（须经权威源 + 对拍 + 签核，禁凭记忆写入）。

## 状态

粗稿（待下一轮开工就地补全为正式规格）
