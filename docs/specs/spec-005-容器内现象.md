# spec-005 · 容器内现象

## 目标

把已派生的 `st.phenomenon.v1` 指令经**表现层变换**渲染为容器内的可观察现象，并以**最小版装置建造**让玩家取器材/药品、倾倒，把「倒入什么 → 求解算出什么状态 → 看到什么现象」的全链路在实验台上闭合。现象由客观状态派生、与求解耗时解耦；表现层只认指令 ID 与物理量。

## 范围

**做**：
- 容器内现象渲染：表现层消费 `st.phenomenon.v1` 指令，实现当前体系已派生类别——指示剂 `color_change` 连续混色、`temperature_change` 可视温升反馈、`splash` 浓硫酸水入酸飞溅。无定量解不出象（求解层派生约束不变）。
- 表现参数变换独立成包：新增 `packages/wasm-view`（Rust→WASM），职责为「指令 → 表现参数」的纯函数变换（颜色插值、飞溅强度、温升强度的归一化计算）；WASM 只认协议指令与物理量，不认分子、不认求解细节。**WASM 不做 Canvas 绘制**。
- 绘制层：React + PixiJS 按表现参数绘制容器内液体与现象；渲染器与求解器可独立替换。
- 现象指令下发：复用 gateway 的 WS phenomenon 订阅通道，把指令推到表现层；同时保留 REST 同源返回供首次渲染与时间轴回放。web-ui 一律经 gateway，不直连求解库。
- 装置建造最小版：可视化实验台，点击取真实器材与药品、摆放、倾倒，选择加入顺序（水入酸 / 酸入水），产出可求解的物质组合输入；作为现象呈现的操作前提。器材参数以 `apparatus` 单一事实源为准。
- 联动与回放：一次操作同时更新现象与物种面板；时间轴回放关键帧时，以帧内现象指令复现现象。
- 浓硫酸飞溅链路：浓硫酸走 `POST /solve/heat`（稀区主求解对浓酸返回 `no_significant_change`），经 gateway `POST /api/v1/heat` 代理并由 WS 下发；水入酸派生 `splash` + `temperature_change`，酸入水同温升但无 `splash`。飞溅仅由加入顺序经安全层派生，整体 ΔT 与方向无关（状态函数）。

**不做**（明确边界）：
- 实验报告（→ spec-006）；图鉴与进度（随 M2 启动，依赖制备/提纯与纯度事实层）。
- 多体系扩张、调度关注度帧预算（→ 体验阶段 / M2）；现象类别注册表随体系接入扩展。
- 完整器材库、复杂装配与 3D 器材（3D 仅分子/晶体/球棍，长线）。
- 虚构物质、用户自定义规则 / MOD / 工坊（红线）。
- 新增现象类别（12 类注册表已覆盖，扩类须升 `schema_version`）。
- 求解层化学逻辑改动（本切片不碰 `solver.py` / `phenomena.py` 的科学口径）。

## 验收标准

1. 表现由客观状态派生：指示剂现象以求解 pH 按 Henderson–Hasselbalch 连续混色（渐变、非阈值跳变），温升有可视反馈；`outcome != solved` 或 `directives` 为空时不绘制现象。
2. 错误操作后果飞溅端到端可达：实验台选择「水入浓酸」经 `/api/v1/heat` 得 `splash` + `temperature_change` 并呈现飞溅；「浓酸入水」同 ΔT 但无 `splash`。黄金用例对指令类型的既有断言继续成立。
3. 装置建造最小交互可取器材/药品、摆放、倾倒并产出合法求解输入；触发后现象与物种面板同步更新，web-ui 不直连求解库。
4. 表现固定 60fps 且与求解耗时解耦：`wasm-view` 为纯同步变换、不触发求解；绘制走浏览器帧循环，求解为异步请求，二者不互相阻塞。`wasm-view` 与 `solver-worker` 经协议 JSON 通信、互不 import。
5. 时间轴回放关键帧时现象可复现：帧内 `phenomena` 指令驱动同一渲染管线，现象与物种快照同步。
6. WS 下发可用：web-ui 订阅 phenomenon 通道并接收指令，与 REST 返回同源一致。
7. 最小充分证据由测试产物承载（见 `03-DocDD-Process.md` 第四节证据自证原则）：`wasm-view` 变换单测（颜色插值边界、飞溅/温升强度归一化、非法指令不崩）、前端构建与类型检查、gateway/求解链既有黄金用例与 e2e 不回归。

## 技术要点

遵循 `01-Architecture.md`：
- 第三节「现象由状态派生」与 `st.phenomenon.v1`：`trigger` 可观测量、`derivation` 派生规则、`intensity` 归一化表现强度（可夸张、不进事实层）。
- 第四节技术栈：`wasm-pack` + `wasm-bindgen`（Rust→WASM 表现参数变换）；表现层 React + PixiJS；`wasm32-unknown-unknown` target 为构建依赖。
- 第五节数据模型：`phenomenon` 类别注册表、`apparatus` 器材参数单一事实源、`compound` 可玩物质卡；近似只作用于视觉/时间尺度，不进化学事实层。
- 第六节依赖规则与包名：`wasm-view`、`web-ui`、`gateway`、`solver-worker`、`protocol` 按本节既有命名；新增 `packages/wasm-view` 属蓝图既有条目，不引入新顶层包。
- 复用切片 003/004 产物：`phenomena.derive()` / `heat_directives()` 派生的指令、`/solve/*` 与 `/api/v1/*` 端点、WS phenomenon 订阅通道、时间轴帧内 `phenomena` 字段、`packages/protocol` 生成的类型。
- 数值口径：表现强度由求解/热结果的物理量归一化得来，不在表现层重算化学量；ΔT、pH、指示剂比值等一律取指令 `physics` 原值。

## 任务拆解

1. **`wasm-view` 表现参数变换包**：新增 `packages/wasm-view`（Rust crate + Cargo.lock），导出纯函数消费 `st.phenomenon.v1` 指令 JSON → 表现参数 JSON（颜色 RGBA、飞溅强度、温升强度、类别可见性）；只认协议字段，不认化学；导出 TS 类型与 WASM 初始化入口。附 Rust 单测覆盖颜色插值边界与强度归一化。
2. **gateway WS 下发闭环**：确认 `/api/v1/heat` 热结果经 WS phenomenon 通道下发；现象订阅与 REST 返回同源同序；不新增化学逻辑。
3. **实验台与绘制层（web-ui）**：新增可视化实验台（器材/药品取用、摆放、倾倒、加入顺序选择），产出求解输入；新增 PixiJS 容器绘制组件消费 `wasm-view` 表现参数；Zustand store 统一经 gateway 取数并订阅 WS；现象与物种面板联动；时间轴回放复现现象。
4. **验证**：`wasm-view` 单测、前端构建与类型检查、黄金用例与 e2e 不回归；任务内跑最小充分证据，产品级门禁由 CI 统一守门。

## 状态

已完成
