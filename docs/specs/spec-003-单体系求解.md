# spec-003 · 单体系求解

> **状态：粗稿**。本稿只定方向与边界，细节留白；开工时在本文件就地补全为正式规格，不另建副本。

## 目标

以切片 002 落地的中和体系事实层为输入，接 phreeqpython 主引擎做动态定量求解，让「取药品 → 任意组合 → 服务端求解 → 数值零错」的下半条链路跑通；同时落地**错误操作后果与涌现发现的最小用例**（错误混合入求解与黄金用例）。

## 范围（大略）

**做**：
- `solver-worker`（Python 3.11）接入 phreeqpython，加载 `content/materialized/ruleset.json`（切片 002 物化产物），对中和体系求解 pH / 物种分布 / 离子强度。
- 与切片 002 黄金用例（`content/golden-cases/neutralization/cases.json`）对拍，逐条断言数值零错。
- chempy 独立对拍主引擎结果（架构第四节对拍链）。
- 错误操作后果最小用例：至少一例错误混合（如浓酸入水放热、密闭体系）入求解/黄金用例，验证后果可零风险重现。
- 物种分布输出契约对齐 `st.solution_speciation.v1`（切片 002 schema），含 `outcome` 出口语义三态。
- 现象派生基座：求解输出的 `ph` / `temperature_K` / 物种浓度供表现层经 `st.phenomenon.v1` 的 `trigger`（可观测状态触发器）派生现象；本切片落地指示剂的 Henderson–Hasselbalch 连续混色（酚酞 pKa 9.1 无色→粉红、甲基橙 pKa 3.46 红→黄，取自权威源快照），确保任意涌现反应产生的 pH 都有可感知视觉反馈。指示剂卡在切片 002 事实层（compound.presentation.indicator），表现映射由状态触发器统一承担，任意反应共享同一套视觉派生机制。

**不做**（明确边界）：
- 物种面板 UI、时间轴、WASM 现象、实验报告（→ spec-004~006）。
- 多体系扩张；本切片只跑中和体系一个体系。
- reaktoro-service 多相/高温高压求解（占位，长线切片）。
- 调度层关注度分数与帧预算（→ 体验阶段）。

## 验收标准（大略，可判定）

1. solver-worker 能加载物化 ruleset 并对中和体系求解；`GET /api/v1/solve`（或内部调用）返回 ph / 物种分布，符合 `st.solution_speciation.v1`。
2. 6 条黄金用例全部数值零错（pH 在容差内、计量守恒、电荷守恒）。
3. 至少 1 条错误操作后果用例通过（错误混合入求解有可复现的定量后果）。
4. chempy 对拍 phreeqpython 主引擎，差异在容差内。
5. 求解失败出口按语义二分，均写入 `st.solution_speciation.v1` 契约：条件不在事实层覆盖范围 → `outcome: "no_significant_change"`（当前条件下无明显变化）；数值不收敛或活度模型超出适用域 → `outcome: "degraded"` 附 `confidence` 与原因（诚实降级），三种出口各自对应真实计算状态。
6. 求解链测试接入 CI：黄金用例对拍由 CI job 执行（与切片 002 的内容校验并列），求解代码变更触发数值零错复核。
7. 求解时延指标：以单次中和体系求解的端到端耗时为对象，设 P95 ≤ 500ms 的首版目标（本地单机、单体系、稳态），实测值写入对拍记录；该指标与渲染帧预算 16.7ms 分属求解与表现两个环节，分别度量。

## 技术要点

遵循 `01-Architecture.md`：
- 定量求解链（第四节）：phreeqpython 主引擎 / chempy 对拍 / SciPy LSODA（本切片快反应用平衡，不引入动力学积分）；无硬编码时间阈值。
- 数据模型第五节：`solution_speciation` 契约；求解缓存内容寻址键（稳态复用，本切片可先不做缓存）。
- 依赖规则第六节：solver-worker 独立 worker，经协议 JSON 通信，不 import web-ui；运行时零网络依赖。
- 红线第七节：事实零错（黄金用例守门）、不造轮子（复用 phreeqpython 内置 `wateq4f_PWN.dat` / `phreeqc.dat`）。
- 活度模型适用域（对齐 01 第五节 5.2）：本切片面向稀水溶液（离子强度 < 0.5 mol/L，Davies/延展 Debye–Hückel 适用域），黄金用例容差在此域内成立；浓区/高离子强度由长线的 `pitzer.dat` 承担，越界时经 `outcome: degraded` 诚实降级，两域口径据此统一。
- 复用切片 002 产物：`schemas/solution_speciation.v1.schema.json`、`content/golden-cases/neutralization/`、`content/ai-crosscheck/neutralization/`。

## 任务拆解

> 粗稿阶段留白——开工时补齐为有序步骤。

## 待开工时确认的方向

> 以下细节刻意不在粗稿锁定，开工时逐一向用户确认后再定：
> - 求解 API 形态（REST 同步 / WS 异步）与是否本切片接入 gateway。
> - 错误操作后果的具体用例（浓酸稀释飞溅 / 密闭加热 / 其他）与定量口径。
> - chempy 对拍的容差阈值。

## 状态

粗稿（待下一轮开工就地补全为正式规格）。
