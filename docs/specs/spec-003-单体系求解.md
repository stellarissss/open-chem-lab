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
- 物种分布输出契约对齐 `st.solution_speciation.v1`（切片 002 schema）。

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
5. 如实记录做了哪些验证、哪些受限（见 `03-DocDD-Process.md` 第四节）。

## 技术要点

遵循 `01-Architecture.md`：
- 定量求解链（第四节）：phreeqpython 主引擎 / chempy 对拍 / SciPy LSODA（本切片快反应用平衡，不引入动力学积分）；无硬编码时间阈值。
- 数据模型第五节：`solution_speciation` 契约；求解缓存内容寻址键（稳态复用，本切片可先不做缓存）。
- 依赖规则第六节：solver-worker 独立 worker，经协议 JSON 通信，不 import web-ui；运行时零网络依赖。
- 红线第七节：事实零错（黄金用例守门）、不造轮子（复用 phreeqpython 内置 `wateq4f_PWN.dat` / `phreeqc.dat`）。
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
