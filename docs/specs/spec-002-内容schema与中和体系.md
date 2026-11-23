# spec-002 · 内容 schema 与中和体系样例

## 目标

建立「可玩物质库 + 静态参数物化层」的最小真实数据与契约，以**酸碱中和体系**为首个样例，把 `01-Architecture.md` 第五节的数据模型从设计落到仓库——让后续求解切片有可加载、可校验、零错签核的事实层输入。

## 范围

**做**：
- 在 `schemas/` 补齐核心实体的 JSON Schema：`compound` / `apparatus` / `reaction_rule` / `solution_speciation`，并由 `@st/protocol` 的 `build:types` 生成 TS 类型（延续切片 001 的契约先行机制）。
- 在 `content/rules/neutralization/` 以**酸碱中和**落一组最小真实数据：6 种可玩物质卡（HCl、HNO₃、NaOH、KOH、醋酸、氨水）+ 条件化反应规则，覆盖 fact / presentation / safety 三层。
- 落地事实层的护栏字段与门禁：`source` / `confidence` / `review`、`applicability`、`data_class`、`rule_revision`；非 verified 不进可玩层、`ml_guess` 禁用。
- 构建期物化链与黄金用例（`content/golden-cases/neutralization/`）：数据可机读、可 diff、可回滚；运行时零网络依赖。
- 权威源快照与 AI 对拍记录（`content/ai-crosscheck/neutralization/`）：USGS PHREEQC `wateq4f.dat` / `minteq.dat` 快照入库，记录 endpoint/license/snapshot_date/sha256 与解析解对拍值。
- Python `jsonschema` 校验门禁：对 `schemas/` 与 `content/rules/` 做构建期校验。`ajv` 仅作为未来浏览器前端候选，不作全局唯一校验器。

**不做**（明确边界）：
- 任何求解逻辑（→ spec-003 单体系求解）。本切片只固化事实层数值与黄金用例的**期望值**，不实现求解器。
- phreeqpython 动态求解调用、物种分布、时间轴、WASM 现象、实验报告、装置搭建交互（→ spec-004~006）。
- 反应规模扩张；本切片只做中和这一个体系的样例，不铺开多体系（规模属后续覆盖阶段）。
- 虚构物质、自制规则、MOD 工坊；未经签核的数值不进事实层。

## 验收标准

1. `schemas/` 新增 4 个核心实体 schema，TS 类型生成成功，`pnpm build` 通过；各语言侧可引用同一事实源。
2. 中和体系样例数据通过 schema 校验；字段完整（source/confidence/applicability 必填），非 verified 不进可玩层，`ml_guess` 被门禁拒绝。
3. 数值经 USGS PHREEQC 权威源 + 解析解对拍 + 用户签核 + 黄金用例才进事实层；计量守恒、条件互斥经核对，数值零错。签核记录见 `content/ai-crosscheck/neutralization/`。
4. 物化层构建期固化、运行时零网络依赖；参数变更走 `rule_revision`、可回滚。

## 技术要点

遵循 `01-Architecture.md`：
- 数据模型（第五节）：`compound` / `apparatus` / `reaction_rule` / `solution_speciation` 字段定义；三类数据分层（fact 零错 / presentation 可夸张标来源 / safety 严谨）；正确性护栏（计量守恒、条件互斥、置信度闸门、来源/对拍/签核完整性、`applicability` 必填、ORD 衍生带 CC-BY-SA 溯源）。
- 权威数据供应链（第五节 5.2）：构建期离线固化 → 候选池 → AI 对拍 → 用户签核 → 黄金用例 → 静态参数层；快照记录 `endpoint / license / snapshot_date / sha256`。
- 工程结构（第六节）：`schemas/` 单一事实源、`content/rules/` 按体系分目录、`content/golden-cases/`、`content/ai-crosscheck/`。
- 红线（第七节）：事实零错、真实库无工坊、CC-BY-SA 数据独立仓、LPPL 只取编译输出物。
- 包/模块命名以 01 第六节为准；schema 文件沿用切片 001 的 `*.v1.schema.json` 命名与 `st.*.v1` 版本常量。

**复用优先**：schema 校验与类型生成沿用切片 001 已建立的 `json-schema-to-typescript` 链；校验用系统已装的 Python `jsonschema`（4.26.0，免新增依赖）；化学参数从 USGS PHREEQC 权威源取，不自造。

**已裁决方向**（开工时用户逐项确认）：
- 体系边界：强弱搭配 6 种（HCl/HNO₃/NaOH/KOH 强酸碱 + 醋酸/氨水弱电解质）。
- 数值来源：抓权威源 + 列清单签核（已签核通过，见 `content/ai-crosscheck/neutralization/`）。
- 校验门禁：Python `jsonschema`；`ajv` 仅未来浏览器前端候选，不作全局唯一校验器。

## 任务拆解

1. 写 `schemas/compound.v1.schema.json`：双语名/分子式/三层数据（fact/presentation/safety）/护栏字段。
2. 写 `schemas/apparatus.v1.schema.json`：容量/刻度/耐温/密封/资产/物理约束。
3. 写 `schemas/reaction_rule.v1.schema.json`：equilibrium/kinetics/thermo 定量 + applicability + numerics + effects + 护栏 + rule_revision。
4. 写 `schemas/solution_speciation.v1.schema.json`：species[]/ph/ionic_strength/equilibria/hidden_reactions。
5. 更新 `packages/protocol/scripts/generate-types.mjs` 与 `src/index.ts`，纳入 4 个新 schema 并生成类型。
6. 落 `content/rules/neutralization/`：6 种物质卡 + 中和反应规则（强弱搭配，fact/presentation/safety 三层）。
7. 落 `content/golden-cases/neutralization/`：黄金用例期望值（pH、守恒、计量）。
8. 落 `content/ai-crosscheck/neutralization/`：权威源快照 + 对拍记录（已完成快照落盘）。
9. 写 Python `jsonschema` 校验门禁脚本，接入 `package.json` 脚本与 CI。
10. 跑验收逐项核对，回写三样产出物。

## 状态

已完成。
