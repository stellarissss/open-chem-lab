"""现象派生（spec-003）：从 solution_speciation 客观状态派生 st.phenomenon.v1 指令。

01 第三节：现象由状态派生——事实层只给物性参数（指示剂 pKa 与两形态色），
表现层按状态实时计算现象。指示剂变色区间由 pKa±1 派生，随求解 pH 渐变而非阈值跳变。

Henderson–Hasselbalch：
    [In-]/[HIn] = 10^(pH - pKa)
    碱式分数 f = ratio / (1 + ratio) ∈ (0,1)  → 直接作为指令 intensity
    表现层按 f 在 acid_color ↔ base_color 间连续混色。
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .solver import load_ruleset


def _indicator_cards(ruleset: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for compound in ruleset.get("compounds", []):
        indicator = (compound.get("presentation") or {}).get("indicator")
        if not indicator:
            continue
        cards.append({
            "compound_id": compound["compound_id"],
            "pka": float(indicator["pka"]),
            "acid_color": indicator["acid_color"],
            "base_color": indicator["base_color"],
        })
    return cards


def indicator_directives(speciation: dict[str, Any], timestamp_ms: int = 0,
                         ruleset: dict[str, Any] | None = None,
                         root: Path | None = None) -> list[dict[str, Any]]:
    """按求解 pH 为每个已签核指示剂产出连续混色现象指令。

    非 solved 出口不产出指令（无定量解就不编造现象）。
    """
    if speciation.get("outcome") != "solved":
        return []
    ruleset = ruleset or load_ruleset(root)
    ph = float(speciation["ph"])
    container_id = speciation["container_id"]
    directives: list[dict[str, Any]] = []

    for idx, card in enumerate(_indicator_cards(ruleset)):
        pka = card["pka"]
        ratio = 10 ** (ph - pka)          # [In-]/[HIn]
        fraction_base = ratio / (1.0 + ratio)
        directives.append({
            "schema_version": "st.phenomenon.v1",
            "directive_id": f"{container_id}-indicator-{card['compound_id']}-{timestamp_ms}",
            "container_id": container_id,
            "type": "color_change",
            "timestamp_ms": timestamp_ms,
            "intensity": round(fraction_base, 6),
            "physics": {
                "ph": ph,
                "pka": pka,
                "acid_color": card["acid_color"],
                "base_color": card["base_color"],
                "indicator_ratio": round(ratio, 6),
            },
            "trigger": {
                "observable": "indicator_ratio",
                "source": "solution_speciation",
                "condition": f"pH={ph:.4f} vs pKa={pka}",
                "derivation": "henderson_hasselbalch",
            },
        })
    return directives


def temperature_directive(speciation: dict[str, Any], timestamp_ms: int = 0) -> dict[str, Any] | None:
    """温度偏离参考 298.15K 时派生 temperature_change 指令（错误操作后果可视反馈）。"""
    if speciation.get("outcome") != "solved":
        return None
    temp = float(speciation.get("temperature_K", 298.15))
    delta = temp - 298.15
    if abs(delta) < 0.5:
        return None
    container_id = speciation["container_id"]
    intensity = min(1.0, abs(delta) / 40.0)
    return {
        "schema_version": "st.phenomenon.v1",
        "directive_id": f"{container_id}-temperature-{timestamp_ms}",
        "container_id": container_id,
        "type": "temperature_change",
        "timestamp_ms": timestamp_ms,
        "intensity": round(intensity, 6),
        "physics": {"temperature_K": temp, "delta_K": round(delta, 4)},
        "trigger": {
            "observable": "temperature_K",
            "source": "solution_speciation",
            "condition": f"delta_K={delta:.4f}",
            "derivation": "delta",
        },
    }


def derive(speciation: dict[str, Any], timestamp_ms: int = 0,
           ruleset: dict[str, Any] | None = None,
           root: Path | None = None) -> list[dict[str, Any]]:
    """统一派生入口：指示剂混色 + 温度变化。"""
    out = indicator_directives(speciation, timestamp_ms, ruleset, root)
    temp = temperature_directive(speciation, timestamp_ms)
    if temp:
        out.append(temp)
    return out
