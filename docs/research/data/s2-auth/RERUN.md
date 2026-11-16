# s2-auth 可重跑实测（阶段二补充规划 · 权威源/缓存源）

> 归档规范见 [`docs/12`](../../../12-阶段二开发流程.md) 第六节。本目录产物均为**可行性原型**，不写产品代码、不进产品构建。
> 决策依据：台账 §9.6 E1–E16；本目录对应 E13（3 组实测）、E14（门禁脚本）。

## 环境

- Python 3.11；`phreeqpython`（自带 USGS PHREEQC 数据库，实测用其 `database/` 目录）。
- 联网组实测需要外网；受限端点（ATcT 403 / SRD46 入口 404）按 `docs/12` §5 纪律**不硬刷、不规避**，如实记录。

## 复跑

```bash
cd docs/research/data/s2-auth
python3 test_auth_snapshot.py     # → auth_snapshot_result.json     （4/4）
python3 test_auth_endpoints.py    # → auth_endpoints_result.json    （5/5，联网）
python3 test_auth_cachekey.py     # → auth_cachekey_result.json     （5/5）
python3 verify_auth_s2.py         # 门禁：全绿退出码 0
```

每组脚本重跑会覆盖同名 JSON；`verify_auth_s2.py` 校验三组 JSON 自洽 + 全仓权威源合规口径。

## 关键结论（供 research/05 引用）

1. **物化主源选择修正（L0）**：`phreeqpython` 自带 `phreeqc.dat` 是压力依赖精简版，仅 3 条显式 log_k；真正适合水溶液物化的是 `wateq4f_PWN.dat`（749 条）/ `pitzer.dat`（94 条）。四库合计 852 条 log_k，注释含 NIST/minteq/WATEQ4F/SUPCRT 溯源。
2. **多版本反应式**：23 个反应式在库内多版本共存（如 `H2O=H2O` 有 log_k 0 与 1.51），印证 E8 内容寻址键**必须带数据源/版本维度**，不能只用反应式名。
3. **可达性**：PubChem PUG-REST 机读 JSON 实测通过（乙醇 C₂H₆O / 46.07），可作构建期离线快照来源；NIST WebBook 仅验算引用（留未来收费权）；ATcT/SRD46 受限，保留复跑路径、运行时零网络依赖（E11）。
4. **缓存键**：内容寻址键确定性、键顺序无关、版本变化即失效；快照四要素完整、篡改可检出，零新中间件（复用 `solve_cache`）。

## 失败项处置留痕（docs/12 §六：失败不得静默丢弃）

- 首版 `test_auth_snapshot.py` 为 2/4 FAIL：①NIST 溯源注释位于 `log_k` 行内 `#` 之后、原解析只读 reaction 行 → 修正为同时捕获 log_k 行内注释；②查表索引用 `(db, reaction)` 作键，遇 23 个多版本反应式相互覆盖 → 修正为 `(db, reaction, occurrence_idx)`。修正后重跑 4/4 PASS，根因与结论已写入 `INDEX.json`。
