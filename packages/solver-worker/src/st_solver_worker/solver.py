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
    "methyl_orange": "MO",  # 指示剂按痕量处理，不主导平衡
    "phenolphthalein": "Phph",
}


def _repo_root() -> Path:
    # src/st_solver_worker/solver.py → 上溯到仓库根
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

    # 仅接受已签核可玩物质；未知物质按"覆盖外"诚实出口
    playable = {c["compound_id"] for c in ruleset.get("compounds", []) if c.get("playable")}
    for sub in substances:
        cid = sub.get("compound_id")
        if cid not in playable or cid not in _ELEMENT_OF:
            return _empty_outcome(container_id, ruleset_version, "no_significant_change",
                                  reason=f"out-of-coverage: {cid}")

    # 汇总元素 mmol（多物质混合，体积按各自 volume_L 折算到 1L 基准）
    totals: dict[str, float] = {}
    for sub in substances:
        element = _ELEMENT_OF[sub["compound_id"]]
        conc = float(sub.get("concentration_mol_L", 0.1))
        vol = float(sub.get("volume_L", 1.0))
        totals[element] = totals.get(element, 0.0) + conc * vol * _MMOL_PER_MOL_L

    try:
        pp = make_phreeq(root)
        solution = pp.add_solution_simple(totals, temperature=temp_K - 273.15)
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
_WATER_MASS_G = 1000.0  # 1L 水 ≈ 1000 g


def neutralization_heat(substances: list[dict[str, Any]],
                        ruleset: dict[str, Any] | None = None) -> dict[str, Any]:
    """强酸 + 强碱混合的绝热温升（错误操作后果，复用 ruleset 的 delta_h）。

    ΔT = |ΔH| × n_neutralized / (m_water × cp)
    n_neutralized = min(强酸 H+ mmol, 强碱 OH- mmol) / 1000
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
    delta_T = abs(dh) * 1000 * n_mol / (_WATER_MASS_G * _WATER_CP)
    return {
        "outcome": "solved",
        "reaction": "H+ + OH- = H2O",
        "delta_h_kj_mol": dh,
        "moles": round(n_mol, 6),
        "delta_T_K": round(delta_T, 4),
        "final_temperature_K": round(298.15 + delta_T, 4),
        "hazard": "强酸入水放热：须酸入水、缓慢搅拌，绝热条件下可致沸腾飞溅",
        "ruleset_version": ruleset.get("ruleset_version", "neutralization-r1"),
        "source": {"kind": "computed", "ref": "ruleset.strong_acid_strong_base.delta_h"},
    }


def solve_heat(compound_ids: list[str] | None = None, ruleset: dict[str, Any] | None = None,
               substances: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """错误操作后果：浓酸/强碱中和放热。兼容旧接口（compound_ids），
    新调用建议传 substances（含浓度/体积）以按实际摩尔数计算。
    """
    if substances is None:
        substances = [
            {"compound_id": cid, "concentration_mol_L": 0.1, "volume_L": 1.0}
            for cid in compound_ids
        ]
    return neutralization_heat(substances, ruleset)

