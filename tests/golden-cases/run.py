#!/usr/bin/env python3
"""中和体系黄金用例 runner（spec-002：固化期望值 + 解析解独立复核）。

本切片不接求解器（→ spec-003），但黄金用例的期望值不能是凭空的数字：
本 runner 用与权威源对拍一致的解析解独立复算每条期望，证明「数值零错」
不是口号。求解层接入后，本 runner 扩展为「求解输出 vs 期望」对拍。

用法：python3 tests/golden-cases/run.py [repo_root]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def weak_acid_ph(ka: float, c: float) -> float:
    h = (-ka + math.sqrt(ka * ka + 4 * ka * c)) / 2
    return -math.log10(h)


def weak_base_ph(kb: float, c: float) -> float:
    oh = (-kb + math.sqrt(kb * kb + 4 * kb * c)) / 2
    return 14.0 + math.log10(oh)


def check(case: dict) -> bool:
    cid = case["case_id"]
    exp = case["expect"]
    setup = case["setup"]
    c = setup.get("concentration_mol_L", 0.1)

    if cid == "strong_acid_0.1M_ph":
        return abs(-math.log10(c) - exp["ph"]) <= exp["tolerance"]
    if cid == "strong_base_0.1M_ph":
        return abs((14.0 + math.log10(c)) - exp["ph"]) <= exp["tolerance"]
    if cid == "weak_acetic_0.1M_ph":
        return abs(weak_acid_ph(10 ** -4.760, c) - exp["ph"]) <= exp["tolerance"]
    if cid == "weak_ammonia_0.1M_ph":
        return abs(weak_base_ph(10 ** -4.748, c) - exp["ph"]) <= exp["tolerance"]
    if cid == "strong_acid_base_equivalence_ph":
        return abs(7.0 - exp["ph"]) <= exp["tolerance"] and exp.get("charge_balance") and exp.get("mass_balance")
    if cid == "weak_acid_strong_base_equivalence_ph_gt_7":
        # 弱酸强碱计量点生成 CH3COO-，水解呈碱性：pH > 7
        ka = 10 ** -4.760
        kb = 10 ** -14 / ka
        salt_c = c / 2  # 等体积混合稀释一半
        return weak_base_ph(kb, salt_c) > exp["ph_gt"]
    fail(f"未知用例 {cid}")
    return False


errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
    path = root / "content" / "golden-cases" / "neutralization" / "cases.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for case in data["cases"]:
        ok = check(case)
        print(f"[golden] {'PASS' if ok else 'FAIL'} {case['case_id']}")
        if not ok:
            fail(case["case_id"])
        n += 1
    if errors:
        print(f"[golden] 失败 {len(errors)}: {errors}", file=sys.stderr)
        return 1
    print(f"[golden] 通过：{n}/{n} 条期望值经解析解独立复核，数值零错")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
