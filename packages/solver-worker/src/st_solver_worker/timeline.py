"""滴定关键帧时间轴产出（spec-004）。

确定性扫描：对已签核的中和体系做「滴定剂体积分数」等距采样，逐帧调用
`solver.solve()`（切片 003 主引擎，不重写求解逻辑），把 `st.solution_speciation.v1`
投影为 `st.timeline.v1` 关键帧与 pH 曲线，供物种面板时间轴回放。

数值口径（不引入新约定）：
- 每帧总「体积」固定 1.0 L：analyte_volume_L = 1 - titrant_volume_L。
  这与切片 003 黄金用例完全同形，因此扫描自然穿过三个签核锚点：
  强酸/强碱体系的 titrant=0、0.5、1.0 分别回指 strong_acid_0.1M_ph、
  strong_acid_base_equivalence_ph、strong_base_0.1M_ph；
  弱酸体系的 0、0.5 回指 weak_acetic_0.1M_ph 与
  weak_acid_strong_base_equivalence_ph_gt_7。
- pH 一律取求解器的活度口径；`outcome != solved` 的帧不派生现象指令。
- 时间轴 timestamp_ms 是仿真相对显示刻度（每帧 1000ms），只服务回放节奏，
  不声称真实反应速率——近似只作用于视觉/时间尺度，不进化学事实层。

字段投影（`01-Architecture.md` 第五节）：
    solution_speciation.species[].species_id          -> timeline.species[].name
    solution_speciation.species[].concentration_mol_L -> timeline.species[].concentration_mol_l
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from . import phenomena, solver

# 仿真回放刻度：每关键帧间隔（毫秒），仅用于回放节奏。
FRAME_INTERVAL_MS = 1000

# 已签核的滴定扫描体系。浓度与黄金用例一致（0.1M），总容积 1.0L。
SCAN_SYSTEMS: dict[str, dict[str, str]] = {
    "strong": {"analyte": "hcl", "titrant": "naoh", "label": "强酸—强碱滴定"},
    "weak": {"analyte": "acetic_acid", "titrant": "naoh", "label": "弱酸—强碱滴定"},
}

# 滴定剂体积分数（含三个黄金锚点 0 / 0.5 / 1.0）。
DEFAULT_RATIOS: tuple[float, ...] = (0.0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9, 1.0)


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _project(spec: dict[str, Any], timestamp_ms: int) -> dict[str, Any]:
    """solution_speciation -> timeline.SpeciationSnapshot（显式字段映射）。"""
    snapshot: dict[str, Any] = {
        "ph": spec["ph"],
        "ionic_strength": spec["ionic_strength"],
        "species": [
            {
                "name": s["species_id"],
                "concentration_mol_l": s["concentration_mol_L"],
                "phase": "aq",
            }
            for s in spec.get("species", [])
        ],
        "outcome": spec.get("outcome", "solved"),
    }
    if "temperature_K" in spec:
        snapshot["temperature_K"] = spec["temperature_K"]
    if "confidence" in spec:
        snapshot["confidence"] = spec["confidence"]
    if spec.get("hidden_reactions"):
        snapshot["hidden_reactions"] = spec["hidden_reactions"]
    snapshot["timestamp_ms"] = timestamp_ms
    return snapshot


def build_timeline(
    system: str = "strong",
    ratios: tuple[float, ...] | None = None,
    container_id: str = "titration-beaker",
    ruleset: dict[str, Any] | None = None,
    root: Any = None,
) -> tuple[dict[str, Any], int]:
    """产出一条 st.timeline.v1。返回 (timeline, solve_calls)。

    solve_calls 供缓存复用实证：N 个关键帧 = N 次求解，无隐藏重复计算。
    """
    if system not in SCAN_SYSTEMS:
        raise ValueError(f"unknown scan system: {system}; choose from {list(SCAN_SYSTEMS)}")
    ratios = DEFAULT_RATIOS if ratios is None else tuple(ratios)
    ruleset = ruleset or solver.load_ruleset(root)
    ruleset_version = ruleset.get("ruleset_version", "neutralization-r1")
    cfg = SCAN_SYSTEMS[system]

    scan_def = {
        "system": system,
        "analyte": cfg["analyte"],
        "titrant": cfg["titrant"],
        "concentration_mol_L": 0.1,
        "total_volume_L": 1.0,
        "ratios": list(ratios),
    }
    timeline_id = hashlib.sha256(
        (_canonical(scan_def) + "|" + ruleset_version).encode("utf-8")
    ).hexdigest()[:16]

    keyframes: list[dict[str, Any]] = []
    ph_points: list[list[int | float]] = []
    species_points: dict[str, list[list[int | float]]] = {}
    solve_calls = 0

    for idx, ratio in enumerate(ratios):
        ratio = round(float(ratio), 6)
        substances: list[dict[str, Any]] = []
        if ratio < 1.0:
            substances.append({
                "compound_id": cfg["analyte"],
                "concentration_mol_L": 0.1,
                "volume_L": round(1.0 - ratio, 6),
            })
        if ratio > 0.0:
            substances.append({
                "compound_id": cfg["titrant"],
                "concentration_mol_L": 0.1,
                "volume_L": ratio,
            })

        spec = solver.solve({"container_id": container_id, "substances": substances}, ruleset, root)
        solve_calls += 1
        ts = idx * FRAME_INTERVAL_MS
        snapshot = _project(spec, ts)
        # 成因溯源随关键帧保留：非 solved 出口不派生现象（诚实降级）。
        if spec.get("outcome") == "solved":
            snapshot["phenomena"] = phenomena.derive(spec, ts, ruleset, root)
        keyframes.append({"timestamp_ms": ts, "container_id": container_id, "speciation": snapshot})

        ph_points.append([ts, spec["ph"]])
        for sp in spec.get("species", []):
            sid = sp["species_id"]
            points = species_points.setdefault(sid, [])
            points.append([ts, sp["concentration_mol_L"]])

    curves: list[dict[str, Any]] = [{"species": "ph", "points": ph_points}]
    for sid in sorted(species_points):
        curves.append({"species": sid, "points": species_points[sid]})

    timeline: dict[str, Any] = {
        "schema_version": "st.timeline.v1",
        "timeline_id": timeline_id,
        "ruleset_version": ruleset_version,
        "keyframes": keyframes,
        "curves": curves,
    }
    return timeline, solve_calls
