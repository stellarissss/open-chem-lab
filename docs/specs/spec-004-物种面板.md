# spec-004 · 物种面板

## 目标

把切片 003 求解产出的 `st.solution_speciation.v1`（物种分布 / pH / 离子强度 / 三态出口）呈现为实验台的物种面板，并以**预生成的确定性滴定扫描**提供关键帧时间轴回放，让隐藏化学态「不可见但真实发生」变得可观察、可追溯、数值不失真。

## 范围

**做**：
- 物种面板视图：读取单个容器的 `solution_speciation`，以**定量 + 诚实提示**口径展示物种浓度/活度、pH、离子强度，以及 `outcome` 三态（solved / no_significant_change / degraded）提示与降级置信度。物种按浓度呈现，不加工、不美化数值；`hidden_reactions` 单列，标明「不可见但真实发生」。
- 时间轴回放：由求解器对**已签核中和体系**做确定性滴定扫描（等当量比等距采样）产出 `st.timeline.v1` 关键帧与 pH 曲线；回放按关键帧读取，稳态复用求解输出、不重复求解。接口同时预留给 spec-005 接入操作录制式时间轴。
- 经 gateway 暴露物种读取与时间轴读取接口（遵循「web-ui 经 gateway 访问、不直连求解库」）；gateway 对预生成时间轴按内容寻址键缓存。
- 现象联动（按用户裁决）：面板依据求解输出的 `st.phenomenon.v1` `trigger` **展示现象成因溯源**（指示剂 pH vs pKa、Henderson–Hasselbalch 分数、温升来源），并在 gateway WS 预留现象推送通道；本切片不渲染现象（渲染归 spec-005）。

**不做**（明确边界）：
- WASM 现象渲染与装置建造交互（→ spec-005）；面板内不绘制液体/气泡/沉淀等容器现象。
- 实验报告（→ spec-006）；图鉴与进度（随 M2 启动，依赖制备/提纯与纯度事实层）。
- 操作录制式时间轴的采集与写入（→ spec-005，本切片只预留接口契约）。
- 多体系扩张、调度关注度帧预算（→ 体验阶段 / M2）；滴定扫描只用已签核的中和体系。
- 虚构物种或近似数值；近似只作用于视觉时间尺度，不进事实层。

## 验收标准

1. gateway 提供物种读取接口与时间轴读取接口，返回体分别符合 `st.solution_speciation.v1` 与 `st.timeline.v1`（经 schema 校验）；web-ui 仅经 gateway 取数，不直连求解库。
2. 中和黄金用例集（`content/golden-cases/neutralization/cases.json`，条数以该文件为准）的求解输出可在面板正确呈现（pH、物种浓度/活度、三态出口），数值不失真；滴定扫描的每一关键帧均为求解器真实输出，等当点 pH 回指黄金用例 `strong_acid_base_equivalence_ph`。
3. 时间轴关键帧可按时间/当量比定位回放；同一体系重复请求命中缓存、不重复求解（以求解调用计数或缓存命中标记佐证）。
4. `outcome` 三态在面板有区分呈现：`degraded` 附置信度提示，`no_significant_change` 明示「当前条件下无明显变化」，不把数值失败表述为科学结论。
5. 现象 trigger 溯源可见：指示剂给出 pH/pKa 与 H-H 分数、温升给出来源；WS 存在现象推送通道（本切片不要求渲染）。
6. 最小充分证据由测试产物承载（见 `03-DocDD-Process.md` 第四节证据自证原则）：schema 校验、黄金用例对拍、缓存复用与前端构建的实测结果。

## 技术要点

遵循 `01-Architecture.md`：

- **数据模型（第五节）**：`solution_speciation` / `speciation_timeline` 契约。注意投影字段差异——`solution_speciation.species[]` 为 `species_id` / `concentration_mol_L`，`timeline.SpeciationSnapshot.species[]` 为 `name` / `concentration_mol_l`；生成关键帧时按契约显式映射，不改 schema。
- **依赖规则（第六节）**：`protocol` 为最底层类型源，`web-ui` 一律经 gateway；`solver-worker`（Python）经 JSON 协议通信，不新增 web-ui→solver 直连。复用 `packages/protocol` 已生成的 `SolutionSpeciation` / `SpeciationTimeline` / `PhenomenonDirective` 类型。
- **复用切片 003 产物**：`solver.solve()` 产出 `solution_speciation`、`phenomena.derive()` 产出现象指令；滴定扫描只在其上循环调用，不重写求解逻辑，不硬编码化学参数。
- **权威数值口径**：扫描输入浓度/体积来自已签核 ruleset 与黄金用例，pH 取活度口径；`minteq.dat.snapshot` 为唯一数值真理源。
- **缓存**：沿用 `01` 第五节 5.2 的内容寻址思路，键取 `sha256(system canonical + ruleset_version + solver_ver)`；本切片以 gateway 进程内缓存落地，零新中间件。
- **诚实降级**：`outcome != solved` 的帧不派生现象指令、不编造物种数值。

## 任务拆解

1. **滴定扫描与关键帧产出**（solver-worker）：新增扫描函数对 HCl+NaOH、乙酸+NaOH 两个已签核体系做等当量比等距采样，逐帧调 `solver.solve()` 投影为关键帧、聚合 pH 曲线，产出 `st.timeline.v1`；新增本地 HTTP 端点 `/solve/timeline`；附带求解调用计数供缓存复用佐证。
2. **gateway 接口与缓存**：新增物种读取（`POST /api/v1/speciation`，代理求解 + 现象派生）与时间轴读取（`GET /api/v1/timeline?system=...`）接口，进程内内容寻址缓存；WS 增加现象推送的订阅/预留消息类型（不渲染）。
3. **web-ui 面板与时间轴**：新增物种面板组件（物种浓度/活度表、pH、离子强度、三态徽章、隐藏反应单列）、时间轴回放控件（关键帧定位 + pH 曲线）、现象 trigger 溯源区；Zustand store 统一经 gateway 取数。
4. **验证**：schema 校验、黄金用例对拍、缓存复用实证、前端构建与类型检查。

## 状态

已完成
