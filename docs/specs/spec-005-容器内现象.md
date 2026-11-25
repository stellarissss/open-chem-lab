# spec-005 · 容器内现象

> **状态：粗稿**。本稿只定方向与边界，细节留白；开工时在本文件就地补全为正式规格，不另建副本。

## 目标

把切片 003 派生的 `st.phenomenon.v1` 现象指令经 WASM 渲染为容器内的可观察现象（液体、气泡、沉淀、火焰、飞溅、指示剂连续混色、温升），并以最小版装置建造交互让玩家取器材、摆放、倾倒，把「倒入什么 → 求解算出什么状态 → 看到什么现象」的全链路在实验台上闭合。

## 范围（大略）

**做**：
- 容器内现象渲染：以 `wasm-view` 消费 `st.phenomenon.v1` 指令，实现当前体系已派生类别（至少 color_change 连续混色、temperature_change 可视反馈、`splash` 浓硫酸水入酸飞溅），指令驱动、与求解耗时解耦。
- 错误操作后果飞溅链路：把 `solve_heat()` 热结果经 `phenomena.heat_directives()` 派生为 `splash` + `temperature_change` 指令——浓硫酸属浓区不进稀区平衡，走 `POST /solve/heat`（非主 `solve()`，后者对浓酸返回 `no_significant_change`）；gateway 经 `POST /api/v1/heat` 代理并经 WS phenomenon 通道下发，表现层只认指令 ID 与物理量。飞溅仅由 `addition_order=water_into_acid` 经安全层派生，两方向整体 ΔT 相同（状态函数）。
- 现象指令下发：经 gateway 的 WS phenomenon 订阅通道（切片 004 已预留）把指令推到表现层；web-ui 只认现象 ID 与物理量，不认分子与求解细节。
- 装置建造最小版：实验台取真实器材与药品、摆放、倾倒，产出可求解的物质组合输入；作为现象呈现的操作前提。
- 与物种面板/时间轴联动：一次操作同时更新现象与物种面板，时间轴回放关键帧时现象可复现。

**不做**（明确边界）：
- 实验报告 / 图鉴与进度（→ spec-006）。
- 多体系扩张、调度关注度帧预算（→ 体验阶段 / M2）；现象类别注册表随体系接入扩展。
- 完整器材库、复杂装配与 3D 器材（3D 仅分子/晶体/球棍，长线）。
- 虚构物质、用户自定义规则 / MOD / 工坊（红线）。

## 验收标准（大略，可判定）

1. 现象由客观状态派生：指示剂随求解 pH 按 Henderson–Hasselbalch 连续混色（渐变而非阈值跳变），温升有可视反馈；无定量解时不出现象。
2. 错误操作后果飞溅端到端可达：触发「水入浓酸」得 `splash` + `temperature_change` 指令并呈现飞溅；「浓酸入水」同温升但无 splash 指令（黄金用例断言指令类型）。浓硫酸走 `/solve/heat` 专用路径，不进稀区主求解。
3. 装置建造最小交互可取器材/药品、摆放、倾倒并产出合法求解输入，触发后现象与物种面板同步更新。
4. 表现固定 60fps 且与求解耗时解耦；WASM 只认 `st.phenomenon.v1` 指令，渲染器与求解器可独立替换。
5. 时间轴回放关键帧时现象可复现；WS 经 gateway 下发，web-ui 不直连求解库（依赖规则）。
6. 最小充分证据由测试产物承载（见 `03-DocDD-Process.md` 第四节证据自证原则）。

## 技术要点

遵循 `01-Architecture.md`：
- 第三节「现象由状态派生」与 `st.phenomenon.v1` 协议：`trigger` 可观测量、`derivation` 派生规则、intensity 为归一化表现强度（可夸张、不进事实层）。
- 第四节技术栈：wasm-pack + wasm-bindgen（Rust→WASM 现象渲染）；表现层 React + PixiJS；`wasm32-unknown-unknown` target 按需 `rustup target add`。
- 第五节数据模型：`phenomenon` 十二类现象注册表、`apparatus` 器材参数单一事实源、`compound` 可玩物质卡；近似只作用于视觉/时间尺度，不进化学事实层。
- 第六节依赖规则：`wasm-view` 与 `solver-worker` 经协议 JSON 通信、互不 import；`web-ui` 一律经 gateway；包/模块命名以本节为准，需偏差先询问。
- 复用切片 004 产物：gateway WS phenomenon 订阅通道、phenomenon 端点、时间轴关键帧的现象派生；切片 003 的 `phenomena.derive()` 输出。

## 状态

粗稿（待下一轮开工就地补全为正式规格）。
