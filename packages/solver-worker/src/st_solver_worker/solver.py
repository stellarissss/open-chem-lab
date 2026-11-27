"""中和体系求解内核（spec-003）。

职责：把「物质组合 + 条件」经 phreeqpython 主引擎（权威源 .dat 快照）求解为
st.solution_speciation.v1 契约输出。活度域口径统一（01 第五节 5.2）：

- pH 取 phreeqpython 的活度 pH（s.pH，Davies/延展 Debye–Hückel），非理想浓度解。
- 权威源 .dat 快照是唯一数值真理源；化学计量只从物化 ruleset 读取，不硬编码。
- 输出三态出口 outcome（01 科学边界）：
    solved              覆盖范围内给出定量解
    no_significant_change  条件不在事实层覆盖范围（合法结论）
    degraded            数值不收敛或活度模型超适用域（I >= 0.5），附 confidence
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

from phreeqpython import PhreeqPython

# 单位换算：输入浓度 mol/L → phreeqpython add_solution_simple 的 mmol（默认水 1L）
_MMOL_PER_MOL_L = 1000.0
# 活度模型适用域上限（01 第五节 5.2：稀区 Davies，浓区 pitzer 长线）
_ACTIVITY_I_LIMIT = 0.5
# 期望物种到 phreeqpython 元素的映射（仅中和体系已签核物质）
# 中南物质卡 formula → 求解输入元素；强电解质用配对离子避免电荷失衡。
_ELEMENT_OF: dict[str, str] = {
    "hcl": "Cl",
    "hno3": "NO3",
    "naoh": "Na",
    "koh": "K",
    "acetic_acid": "Acetate",
    "ammonia": "NH3",
}
# 指示剂 compound_id：痕量探针，不参与平衡求解（权威源 .dat 未定义其平衡），
# 只记录到 indicators 供现象派生；倒什么看什么，且不以伪元素破坏求解收敛。
_INDICATOR_IDS = {"methyl_orange", "phenolphthalein"}
# 溶剂 compound_id：水是溶剂（化学计量基准 1kg 水本身），不贡献溶质元素，
# 但贡献体积参与归一——加水稀释时溶质浓度被正确稀释。水作为特例走纯水温度路径。
_SOLVENT_IDS = {"water"}


def _repo_root() -> Path:
    # 容器部署时仓库根为 /app（Dockerfile 把 content/ 与 src/ 平级放置），
    # 本地开发时从 src/st_solver_worker/solver.py 上溯四层到仓库根。
    override = os.environ.get("ST_REPO_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[4]


def load_ruleset(root: Path | None = None) -> dict[str, Any]:
    root = root or _repo_root()
    path = root / "content" / "materialized" / "ruleset.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _database_dir(root: Path | None = None) -> Path:
    """权威源 .dat 快照目录（ai-crosscheck neeutralization）。"""
    root = root or _repo_root()
    return (root / "content" / "ai-crosscheck" / "neutralization").resolve()


def _database_name() -> str:
    """minteq.dat 覆盖乙酸解离（wateq4f 缺乙酸定义），为中和体系权威源主库。"""
    return "minteq.dat.snapshot"


def make_phreeq(root: Path | None = None) -> PhreeqPython:
    return PhreeqPython(database=_database_name(), database_directory=_database_dir(root))


def solve_pure_water(temp_C: float, root: Path | None = None) -> Any:
    """纯水（无溶质）专用求解：走 PHREEQC 原生 SOLUTION + -temp，温度依赖正确。

    根因：phreeqpython 的 add_solution_simple({}) 空组成路径不建立配平水溶液，
    pH 恒返回 7.0，导致纯水在 25°C 外的中性点科学错误（100°C 应约 6.02）。
    权威 .dat 的水解离带 delta_h 13.345 kcal，PHREEQC 原生输入能正确算温度依赖，
    实测与 IAPWS 中性点序列吻合（0°C 7.45 / 25°C 7.00 / 100°C 6.02）。
    返回与 add_solution_simple 同构的 Solution 对象（pH/I/molality/activity/species）。
    """
    pp = make_phreeq(root)
    inp = (
        "SOLUTION 1\n"
        f"-temp {temp_C}\n"
        "units mmol/L\n"
        "pH 7 charge\n"
        "SAVE SOLUTION 1\n"
        "END\n"
    )
    pp.ip.run_string(inp)
    return pp.get_solution(1)


def _empty_outcome(container_id: str, ruleset_version: str, outcome: str,
                   confidence: float | None = None, reason: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": "st.solution_speciation.v1",
        "speciation_id": hashlib.sha256(
            f"{container_id}:{outcome}:{reason}".encode("utf-8")
        ).hexdigest()[:16],
        "container_id": container_id,
        "species": [],
        "ph": 7.0,
        "ionic_strength": 0.0,
        "outcome": outcome,
        "ruleset_version": ruleset_version,
        "source": {"kind": "solver", "ref": "phreeqpython/minteq.dat.snapshot"},
    }
    if confidence is not None:
        result["confidence"] = confidence
    # 诚实降级：把原因写进契约输出（spec-003 承诺 degraded 附 confidence 与原因）。
    if reason:
        result["reason"] = reason
    return result


def solve(system: dict[str, Any], ruleset: dict[str, Any] | None = None,
          root: Path | None = None) -> dict[str, Any]:
    """对一组物质求解中和体系。

    system 形状（内部 JSON 契约）：
        {
          "container_id": "beaker-1",
          "substances": [
            {"compound_id": "hcl", "concentration_mol_L": 0.1, "volume_L": 1.0}
          ],
          "temperature_K": 298.15
        }
    体积用于混合稀释：各物质 mmol = concentration * volume_L * 1000，
    phreeqpython 默认溶剂 1 kg 水，故总摩尔按实际 volume 缩放后除以总体积归一。
    """
    ruleset = ruleset or load_ruleset(root)
    container_id = system.get("container_id", "default")
    ruleset_version = ruleset.get("ruleset_version", "neutralization-r1")
    substances = system.get("substances", [])
    temp_K = float(system.get("temperature_K", 298.15))

    if not substances:
        return _empty_outcome(container_id, ruleset_version, "no_significant_change",
                              reason="empty system")

    # 仅接受已签核可玩物质；未知物质按"覆盖外"诚实出口。
    # 指示剂虽无平衡元素，但属已签核可玩探针，允许通过（只进 indicators）。
    playable = {c["compound_id"] for c in ruleset.get("compounds", []) if c.get("playable")}
    for sub in substances:
        cid = sub.get("compound_id")
        allowed = cid in _ELEMENT_OF or cid in _INDICATOR_IDS or cid in _SOLVENT_IDS
        if cid not in playable or not allowed:
            return _empty_outcome(container_id, ruleset_version, "no_significant_change",
                                  reason=f"out-of-coverage: {cid}")

    # 实际加入的指示剂（痕量探针，供现象派生：只对加入的指示剂派生变色，倒什么看什么）
    indicators = [s["compound_id"] for s in substances
                  if s["compound_id"] in _INDICATOR_IDS]

    # 汇总元素 mmol，并归一到 phreeqpython 的固定 1kg 水基准。
    # pH 是强度量，只取决于浓度 = 总物质的量 / 总体积，与绝对体积无关。
    # 先按各自体积折算实际物质的量（mmol），再除以总体积得到「1L 基准的 mmol」：
    #   total_mmol / total_volume_L == Σ(conc_i × vol_i) / Σ(vol_i) × 1000
    # 缺此归一会让 0.1M×2L 被当成 0.2M（pH 从 1.08 错到 0.80），违反事实零错。
    # 指示剂是被动探针，不贡献体积基准也不参与平衡。
    reactive = [s for s in substances if s["compound_id"] not in _INDICATOR_IDS]
    total_volume_L = sum(float(s.get("volume_L", 1.0)) for s in reactive)
    if total_volume_L <= 0:
        return _empty_outcome(container_id, ruleset_version, "degraded",
                              confidence=0.2, reason="non-positive reactive volume")
    totals: dict[str, float] = {}
    for sub in reactive:
        cid = sub["compound_id"]
        if cid in _SOLVENT_IDS:
            # 溶剂（水）不贡献溶质元素，只贡献体积；体积已在 total_volume_L 计入。
            continue
        element = _ELEMENT_OF[cid]
        conc = float(sub.get("concentration_mol_L", 0.1))
        vol = float(sub.get("volume_L", 1.0))
        total_mmol = conc * vol * _MMOL_PER_MOL_L
        totals[element] = totals.get(element, 0.0) + total_mmol / total_volume_L

    temp_C = temp_K - 273.15
    try:
        if not totals:
            # 纯水/仅溶剂：走原生 SOLUTION 路径，温度依赖正确（add_solution_simple({}) 恒 pH 7）。
            solution = solve_pure_water(temp_C, root)
        else:
            # 含溶质：REACTION 路径正确（氨水/乙酸等中性物种靠它平衡），稀释已由体积归一处理。
            pp = make_phreeq(root)
            solution = pp.add_solution_simple(totals, temperature=temp_C)
        ph = float(solution.pH)          # 活度口径（主文档裁决）
        ionic = float(solution.I)
    except Exception as exc:  # 数值不收敛 → 诚实降级
        return _empty_outcome(container_id, ruleset_version, "degraded",
                              confidence=0.3, reason=f"non-convergence: {exc}")

    if ionic >= _ACTIVITY_I_LIMIT:
        return _empty_outcome(container_id, ruleset_version, "degraded",
                              confidence=0.4,
                              reason=f"ionic strength {ionic:.3f} >= {_ACTIVITY_I_LIMIT} (Davies domain)")

    species = [
        {
            "species_id": sp,
            "concentration_mol_L": float(solution.molality(sp)) / _MMOL_PER_MOL_L,
            "activity": float(solution.activity(sp)) / _MMOL_PER_MOL_L,
        }
        for sp in solution.species
        if sp in ("H+", "OH-", "Acetate", "HAc", "NH4+", "NH3", "Na+", "K+", "Cl-", "NO3-")
    ]

    # 错误操作后果：强酸+强碱混合的中和放热回写 temperature_K，
    # 使状态派生能产出 temperature_change 现象（"错误混合入求解"）。
    heat = neutralization_heat(substances, ruleset)
    final_temp_K = heat["final_temperature_K"] if heat["outcome"] == "solved" else temp_K

    result: dict[str, Any] = {
        "schema_version": "st.solution_speciation.v1",
        "speciation_id": hashlib.sha256(
            json.dumps(system, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16],
        "container_id": container_id,
        "species": species,
        "ph": ph,
        "ionic_strength": ionic,
        "outcome": "solved",
        "temperature_K": final_temp_K,
        "equilibria": [r["rule_id"] for r in ruleset.get("reaction_rules", [])
                       if r.get("system") == "neutralization"],
        "hidden_reactions": ["water_dissociation"],
        "indicators": indicators,
        "ruleset_version": ruleset_version,
        "source": {
            "kind": "solver",
            "ref": "phreeqpython/minteq.dat.snapshot",
            "version": "minteq-2024",
            "snapshot_date": "2026-11-22",
        },
    }
    if heat["outcome"] == "solved":
        result["physics_note"] = heat["hazard"]
    return result


# 强酸/强碱的配对元素（用于判定中和放热）
_STRONG_ACID_ELEMENTS = {"Cl", "NO3"}
_STRONG_BASE_ELEMENTS = {"Na", "K"}
_WATER_CP = 4.184  # J/(g·K)
_WATER_DENSITY_G_PER_L = 1000.0  # 1L 水 ≈ 1000 g（稀溶液近似）
# 浓硫酸：浓区热效应物质，不进稀区平衡求解。物性来自已签核物质卡。
_CONC_ACID_ID = "sulfuric_acid_conc"
_CONC_ACID_CONC_MOL_L = 18.4  # 约 98% 质量分数，ρ=1.84 g/mL
_CONC_ACID_DENSITY_G_ML = 1.84
_WATER_DENSITY_G_ML = 1.0


def neutralization_heat(substances: list[dict[str, Any]],
                        ruleset: dict[str, Any] | None = None) -> dict[str, Any]:
    """强酸 + 强碱混合的绝热温升（错误操作后果，复用 ruleset 的 delta_h）。

    ΔT = |ΔH| × n_neutralized / (m_water × cp)
    n_neutralized = min(强酸 H+ mmol, 强碱 OH- mmol) / 1000
    m_water = 混合后总体积 × 水密度（1L≈1000g）——固定 1000g 会把 1L+1L 的
    温升高估一倍，违反事实零错，故按实际总体积折算。
    """
    ruleset = ruleset or load_ruleset()
    acid_mmol = sum(
        float(s.get("concentration_mol_L", 0.1)) * float(s.get("volume_L", 1.0)) * _MMOL_PER_MOL_L
        for s in substances if _ELEMENT_OF.get(s.get("compound_id")) in _STRONG_ACID_ELEMENTS
    )
    base_mmol = sum(
        float(s.get("concentration_mol_L", 0.1)) * float(s.get("volume_L", 1.0)) * _MMOL_PER_MOL_L
        for s in substances if _ELEMENT_OF.get(s.get("compound_id")) in _STRONG_BASE_ELEMENTS
    )
    n_mol = min(acid_mmol, base_mmol) / _MMOL_PER_MOL_L
    if n_mol <= 0:
        return {"outcome": "no_significant_change", "reason": "no strong acid/base pair"}

    rule = next((r for r in ruleset.get("reaction_rules", [])
                 if r.get("rule_id") == "strong_acid_strong_base"), None)
    if rule is None:
        return {"outcome": "degraded", "reason": "missing strong_acid_strong_base rule"}
    dh = float(rule["equilibrium"].get("delta_h_kj_mol", -55.84))  # kJ/mol
    # 指示剂为痕量探针，不计入水量（与 solve() 口径一致）
    reactive = [s for s in substances if s.get("compound_id") not in _INDICATOR_IDS]
    total_volume_L = sum(float(s.get("volume_L", 1.0)) for s in reactive)
    water_mass_g = max(total_volume_L, 1.0) * _WATER_DENSITY_G_PER_L
    delta_T = abs(dh) * 1000 * n_mol / (water_mass_g * _WATER_CP)
    return {
        "outcome": "solved",
        "reaction": "H+ + OH- = H2O",
        "delta_h_kj_mol": dh,
        "moles": round(n_mol, 6),
        "total_volume_L": round(total_volume_L, 4),
        "water_mass_g": round(water_mass_g, 4),
        "delta_T_K": round(delta_T, 4),
        "final_temperature_K": round(298.15 + delta_T, 4),
        "hazard": "强酸入水放热：须酸入水、缓慢搅拌，绝热条件下可致沸腾飞溅",
        "ruleset_version": ruleset.get("ruleset_version", "neutralization-r1"),
        "source": {"kind": "computed", "ref": "ruleset.strong_acid_strong_base.delta_h"},
    }


def dilution_heat(substances: list[dict[str, Any]], ruleset: dict[str, Any] | None = None,
                  addition_order: str = "acid_into_water") -> dict[str, Any]:
    """浓硫酸稀释的绝热温升与飞溅风险（错误操作后果，spec-003）。

    物理模型（严格分层，对齐 01 第五节）：
    - 事实层：稀释焓 ΔH 是状态函数，与加入方向无关；总放热 Q = n(H2SO4)·|ΔH|，
      整体绝热温升 ΔT = Q /(m_total·cp)，两种方向数值相同——浓硫酸入水整体温度同样急剧上升。
    - 安全层：飞溅由「加入顺序」派生——水入酸（water_into_acid）时水密度小浮于酸面，
      界面薄层吸收稀释热瞬间闪沸（flash boiling）、裹挟酸液飞溅；酸入水（acid_into_water）
      时酸沉底、热量分散于大水体，不飞溅。这是密度分层 + 局部传热的机制结论，
      不改变放热总量，表现层据此派生 splash 强度（近似，不进事实层）。
    """
    ruleset = ruleset or load_ruleset()
    rule = next((r for r in ruleset.get("reaction_rules", [])
                 if r.get("rule_id") == "sulfuric_acid_dilution"), None)
    if rule is None:
        return {"outcome": "degraded", "reason": "missing sulfuric_acid_dilution rule"}
    dh = float(rule["equilibrium"]["delta_h_kj_mol"])  # kJ/mol，负值放热

    acid = next((s for s in substances if s.get("compound_id") == _CONC_ACID_ID), None)
    if acid is None:
        return {"outcome": "no_significant_change", "reason": "no concentrated sulfuric acid"}
    a_vol_L = float(acid.get("volume_L", 1.0))
    a_conc = float(acid.get("concentration_mol_L", _CONC_ACID_CONC_MOL_L))
    n_mol = a_conc * a_vol_L
    acid_mass_g = a_vol_L * _CONC_ACID_DENSITY_G_ML * _WATER_DENSITY_G_PER_L

    # 水量：其他物质按体积折算为水（本体系只有水与浓硫酸）
    water_vol_L = sum(float(s.get("volume_L", 1.0)) for s in substances
                      if s.get("compound_id") != _CONC_ACID_ID)
    water_mass_g = water_vol_L * _WATER_DENSITY_G_PER_L
    total_mass_g = acid_mass_g + water_mass_g
    if total_mass_g <= 0:
        return {"outcome": "degraded", "reason": "non-positive mass"}

    q_kj = n_mol * abs(dh)
    delta_T = q_kj * 1000 / (total_mass_g * _WATER_CP)
    # 飞溅是安全层派生：由加入顺序这个可观测操作状态驱动，不改放热总量。
    splash_risk = addition_order == "water_into_acid"
    return {
        "outcome": "solved",
        "reaction": "H2SO4 = 2H+ + SO4-2",
        "delta_h_kj_mol": dh,
        "moles": round(n_mol, 6),
        "heat_released_kj": round(q_kj, 4),
        "total_mass_g": round(total_mass_g, 4),
        "delta_T_K": round(delta_T, 4),
        "final_temperature_K": round(298.15 + delta_T, 4),
        "addition_order": addition_order,
        "splash_risk": splash_risk,
        "hazard": ("水入浓硫酸：界面薄层闪沸、酸液飞溅（错误操作）" if splash_risk
                   else "酸入水：整体急剧升温，须缓慢沿壁加入并搅拌；热量分散不飞溅"),
        "ruleset_version": ruleset.get("ruleset_version", "neutralization-r1"),
        "source": {"kind": "computed", "ref": "ruleset.sulfuric_acid_dilution.delta_h"},
    }


def solve_heat(compound_ids: list[str] | None = None, ruleset: dict[str, Any] | None = None,
               substances: list[dict[str, Any]] | None = None,
               addition_order: str = "acid_into_water") -> dict[str, Any]:
    """错误操作后果热效应。浓硫酸稀释走 dilution_heat（方向相关的飞溅风险），
    其余强酸强碱中和走 neutralization_heat。兼容旧接口（compound_ids）。
    """
    if substances is None:
        substances = [
            {"compound_id": cid, "concentration_mol_L": 0.1, "volume_L": 1.0}
            for cid in compound_ids
        ]
    if any(s.get("compound_id") == _CONC_ACID_ID for s in substances):
        return dilution_heat(substances, ruleset, addition_order)
    return neutralization_heat(substances, ruleset)

