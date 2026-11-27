#!/usr/bin/env python3
"""实验报告汇编门禁（spec-006 最小充分证据）。

把验收标准 1/2/3 变成机器可判定：
1. 数值零加工：报告快照 pH/浓度/time轴曲线逐字段等于 solver/timeline 出口原值；
2. 来源引用闭合：每条数值 source_ref 指向 sources[].source_id，反应式 rule_id 回指已签核规则且 equation 一致；
3. 三态出口如实：degraded / no_significant_change 保留 confidence / reason，不冒充定量结论；
4. 幂等：同输入两次生成同一 report_id；
5. 契约合规：产物通过 st.report.v1 schema 校验。

用法：PYTHONPATH=packages/solver-worker/src python3 tests/report/check.py [repo_root]
依赖：jsonschema（系统/venv 均已装，无新增依赖）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:
    print(f"[report-check] 缺少 jsonschema: {exc}", file=sys.stderr)
    raise SystemExit(2)

from st_solver_worker import report, solver, timeline

errors: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        errors.append(msg)


def run(root: Path) -> None:
    ruleset = solver.load_ruleset(root)
    ops = [
        {"seq": 1, "kind": "place_apparatus", "container_id": "b1", "apparatus_id": "beaker_250ml"},
        {"seq": 2, "kind": "pour", "container_id": "b1", "compound_id": "hcl",
         "concentration_mol_L": 0.1, "volume_L": 1.0},
    ]
    substances = [{"compound_id": "hcl", "concentration_mol_L": 0.1, "volume_L": 1.0}]

    built = report.build_report(operations=ops, substances=substances, system="strong",
                                container_id="b1", ruleset=ruleset, root=root)

    # 5. 契约合规
    schema = json.loads((root / "schemas" / "report.v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    verrs = sorted(Draft202012Validator(schema).iter_errors(built), key=lambda e: list(e.path))
    for e in verrs[:5]:
        errors.append(f"schema 校验失败 @{list(e.path)}: {e.message}")

    # 1. 数值零加工：与 solve / timeline 出口逐字段相等
    spec = solver.solve({"container_id": "b1", "substances": substances}, ruleset, root)
    snap = built["snapshots"][0]
    check(snap["ph"] == spec["ph"], f"pH 被加工：报告 {snap['ph']} != 求解 {spec['ph']}")
    check(snap["ionic_strength"] == spec["ionic_strength"], "离子强度被加工")
    rep_sp = {s["name"]: s["concentration_mol_l"] for s in snap["species"]}
    src_sp = {s["species_id"]: s["concentration_mol_L"] for s in spec["species"]}
    check(rep_sp == src_sp, f"物种浓度被加工：{rep_sp} != {src_sp}")
    tdata, _ = timeline.build_timeline(system="strong", ruleset=ruleset, root=root)
    check(built["curves"] == [
        {"species": c["species"], "points": c["points"], "source_ref": "src-timeline"}
        for c in tdata["curves"]
    ], "时间轴曲线被加工或丢失")

    # 2. 来源引用闭合
    ids = {s["source_id"] for s in built["sources"]}
    refs = [snap["source_ref"]] + [s["source_ref"] for s in snap["species"]]
    refs += [c["source_ref"] for c in built["curves"]]
    refs += [r["source_ref"] for r in built["reactions"]]
    dangling = [r for r in refs if r not in ids]
    check(not dangling, f"悬空来源引用：{dangling}")

    # 反应式回指已签核规则，equation 逐字一致
    ridx = {r["rule_id"]: r for r in ruleset["reaction_rules"]}
    for rxn in built["reactions"]:
        rule = ridx.get(rxn["rule_id"])
        check(rule is not None, f"反应式引用未签核规则 {rxn['rule_id']}")
        if rule:
            check(rxn["equation"] == rule["reaction"]["equation"],
                  f"反应式 equation 被改写：{rxn['rule_id']}")

    # 权威源哈希回指 golden cases
    golden = json.loads((root / "content/golden-cases/neutralization/cases.json").read_text(encoding="utf-8"))
    src_solver = next(s for s in built["sources"] if s["source_id"] == "src-solver")
    check(src_solver["sha256"] == golden["database_sha256"], "求解来源哈希未回指权威 .dat 快照")

    # 3. 三态出口如实：覆盖外物质 -> no_significant_change 且保留 reason
    degraded = report.build_report(
        substances=[{"compound_id": "unknown_xyz", "concentration_mol_L": 0.1, "volume_L": 1.0}],
        ruleset=ruleset, root=root)
    dsnap = degraded["snapshots"][0]
    check(dsnap["outcome"] == "no_significant_change", f"覆盖外出口错误：{dsnap['outcome']}")
    check(bool(dsnap.get("reason")), "非 solved 出口缺 reason（未如实降级）")
    check(degraded["outcome_summary"]["no_significant_change"] == 1, "出口汇总未如实计数")

    # 4. 幂等
    again = report.build_report(operations=ops, substances=substances, system="strong",
                                container_id="b1", ruleset=ruleset, root=root)
    check(again["report_id"] == built["report_id"],
          f"同输入 report_id 不一致：{built['report_id']} vs {again['report_id']}")

    print(f"[report-check] report_id={built['report_id']} 快照={snap['outcome']} "
          f"曲线={len(built['curves'])} 反应式={len(built['reactions'])} 来源={len(built['sources'])}")
    print(f"[report-check] 降级出口={dsnap['outcome']}（reason={bool(dsnap.get('reason'))}）")


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
    print(f"[report-check] root: {root}")
    run(root)
    if errors:
        print(f"[report-check] 失败 {len(errors)} 项：", file=sys.stderr)
        for e in errors:
            print(f"  X {e}", file=sys.stderr)
        raise SystemExit(1)
    print("[report-check] 通过：数值零加工、来源引用闭合、反应式回指、三态出口如实、幂等、契约合规")
