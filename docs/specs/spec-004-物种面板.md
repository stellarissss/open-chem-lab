# spec-004 · 物种面板

> **状态：粗稿**。本稿只定方向与边界，细节留白；开工时在本文件就地补全为正式规格，不另建副本。

## 目标

把切片 003 求解产出的 `st.solution_speciation.v1`（物种分布 / pH / 离子强度 / 三态出口）呈现为实验台的物种面板，并支持关键状态的时间轴回放，让隐藏化学态「不可见但真实发生」变得可观察、可追溯。

## 范围（大略）

**做**：
- 物种面板视图：读取单个容器的 `solution_speciation`，展示物种浓度/活度、pH、离子强度，以及 `outcome` 三态（solved / no_significant_change / degraded）的诚实提示。
- 时间轴回放：`speciation_timeline` 关键帧的存取与回放（稳态复用，不重复求解）。
- 经 gateway 暴露 `solution_speciation` 读取接口（遵循「web-ui 经 gateway 访问、不直连求解库」）。
- 求解输出经 `st.phenomenon.v1` 的 `trigger` 与表现层联动（承接 003 的涌现基座）。

**不做**（明确边界）：
- WASM 现象渲染与装置建造交互（→ spec-005）。
- 实验报告 / 图鉴与进度（→ spec-006）。
- 多体系扩张、调度关注度帧预算（→ 体验阶段 / M2）。

## 验收标准（大略，可判定）

1. gateway 提供物种读取接口，返回契约符合 `st.solution_speciation.v1`；web-ui 经 gateway 展示面板。
2. 6 条中和黄金用例的求解输出可在面板正确呈现（pH、物种、三态出口），数值不失真。
3. 时间轴关键帧可回放，稳态复用求解输出、不重复计算。
4. 最小充分证据如实记录（见 `03-DocDD-Process.md` 第四节）。

## 技术要点

遵循 `01-Architecture.md`：
- 数据模型第五节：`solution_speciation` / `speciation_timeline` 契约；`outcome` 三态表现。
- 依赖规则第六节：`web-ui` 不直连求解库、一律经 gateway；`protocol` 为最底层类型源。
- 复用切片 003 产物：`st.solution_speciation.v1` 输出与现象 `trigger` 派生。

## 状态

粗稿（待下一轮开工就地补全为正式规格）。
