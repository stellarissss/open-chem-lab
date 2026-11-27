"""实验报告汇编（spec-006）。

职责边界：**只汇编，不重算化学量**。本模块不实现任何化学逻辑，数值全部取
`solver.solve()` 与 `timeline.build_timeline()` 的既有出口原值，反应式逐条引用
已签核 `reaction_rule`，来源锚点回指权威源快照哈希 / 规则集哈希 / 对拍记录。

产物为 st.report.v1 投影契约（非事实层、不进求解主链）：
- 每条数值以 source_ref 指向 sources[].source_id，引用闭合可机器核验；
- outcome 三态如实呈现，降级附 confidence / reason，不冒充定量结论；
- report_id 为内容寻址 sha256：同输入幂等，不含墙钟时间。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from . import solver, timeline

# 来源锚点固定 ID：引用闭合由 tests/report/check.py 断言。
SOLVER_SRC = "src-solver"
RULESET_SRC = "src-ruleset"
CROSSCHECK_SRC = "src-crosscheck"


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _golden_cases(root: Path) -> dict[str, Any]:
    path = root / "content" / "golden-cases" / "neutralization" / "cases.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _build_sources(
    spec: dict[str, Any],
    timeline_data: dict[str, Any],
    ruleset: dict[str, Any],
    root: Path,
    used_rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """来源锚点全部取自现存文件字段，不硬编码哈希、不臆造来源。"""
    golden = _golden_cases(root)
    db_sha = golden.get("database_sha256")
    src = spec.get("source") or {}
    sources: list[dict[str, Any]] = [
        {
            "source_id": SOLVER_SRC,
            "kind": "solver",
            "ref": src.get("ref", "phreeqpython/minteq.dat.snapshot"),
            "sha256": db_sha,
            "version": src.get("version"),
            "snapshot_date": src.get("snapshot_date"),
            "note": "求解出口原值；活度口径；哈希回指权威 .dat 快照",
        },
        {
            "source_id": RULESET_SRC,
            "kind": "ruleset",
            "ref": "content/materialized/ruleset.json",
            "sha256": ruleset.get("ruleset_sha256"),
            "version": ruleset.get("ruleset_version"),
            "snapshot_date": None,
            "note": "规则集版本与哈希，保证汇编可复现",
        },
        {
            "source_id": "src-timeline",
            "kind": "timeline",
            "ref": f"st.timeline.v1/{timeline_data.get('timeline_id', '')}",
            "sha256": None,
            "version": timeline_data.get("ruleset_version"),
            "snapshot_date": None,
            "note": "时间轴曲线原值，按 timeline_id 可回指",
        },
        {
            "source_id": CROSSCHECK_SRC,
            "kind": "crosscheck",
            "ref": golden.get("source", "content/ai-crosscheck/neutralization/record.json"),
            "sha256": None,
            "version": None,
            "snapshot_date": None,
            "note": "对拍记录：" + ", ".join(
                t.get("name", "") for t in (golden.get("evidence") or {}).get("crosscheck_tools", [])
            ) + " 独立对拍；黄金用例锚定 database_sha256",
        },
    ]
    # 每条被引用规则单独建权威源锚点，sha256 取规则 source.sha256（可为 null，如实呈现）。
    for rule in used_rules:
        rsrc = rule.get("source") or {}
        sources.append({
            "source_id": f"src-rule-{rule['rule_id']}",
            "kind": "authoritative_db",
            "ref": rsrc.get("ref", ""),
            "sha256": rsrc.get("sha256"),
            "version": rsrc.get("version"),
            "snapshot_date": rsrc.get("snapshot_date"),
            "note": f"已签核规则 {rule['rule_id']} 的权威源（{rsrc.get('license', '')}）",
        })
    return sources


def build_report(
    operations: list[dict[str, Any]] | None = None,
    substances: list[dict[str, Any]] | None = None,
    system: str = "strong",
    container_id: str = "report-beaker",
    ruleset: dict[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """汇编 st.report.v1。所有化学数值经 solve/timeline 出口取得，本函数不加工。"""
    root = root or solver._repo_root()
    ruleset = ruleset or solver.load_ruleset(root)
    operations = operations or []

    spec = solver.solve({"container_id": container_id, "substances": substances or []}, ruleset, root)
    timeline_data, _ = timeline.build_timeline(system=system, ruleset=ruleset, root=root)

    # 反应式：取求解出口实际引用的平衡 + 隐藏反应 rule_id，回指已签核规则表。
    rule_index = {r.get("rule_id"): r for r in ruleset.get("reaction_rules", [])}
    cited_ids: list[str] = []
    for rid in list(spec.get("equilibria", [])) + list(spec.get("hidden_reactions", [])):
        if rid in rule_index and rid not in cited_ids:
            cited_ids.append(rid)
    used_rules = [rule_index[rid] for rid in cited_ids]

    reactions: list[dict[str, Any]] = [
        {
            "rule_id": r["rule_id"],
            "equation": r["reaction"]["equation"],
            "data_class": r.get("data_class"),
            "confidence_level": (r.get("confidence") or {}).get("level"),
            "source_ref": f"src-rule-{r['rule_id']}",
        }
        for r in used_rules
    ]

    # 快照：数值逐字段原样取自 solve 出口；非 solved 出口如实保留 confidence / reason。
    snapshot: dict[str, Any] = {
        "container_id": container_id,
        "outcome": spec.get("outcome", "solved"),
        "source_ref": SOLVER_SRC,
        "species": [
            {
                "name": s["species_id"],
                "concentration_mol_l": s["concentration_mol_L"],
                "source_ref": SOLVER_SRC,
            }
            for s in spec.get("species", [])
        ],
    }
    for key in ("ph", "ionic_strength", "temperature_K", "confidence", "reason"):
        if key in spec:
            snapshot[key] = spec[key]

    curves: list[dict[str, Any]] = [
        {
            "species": c["species"],
            "points": c["points"],
            "source_ref": "src-timeline",
        }
        for c in timeline_data.get("curves", [])
    ]

    sources = _build_sources(spec, timeline_data, ruleset, root, used_rules)
    outcome = snapshot["outcome"]
    summary = {
        "solved": 1 if outcome == "solved" else 0,
        "no_significant_change": 1 if outcome == "no_significant_change" else 0,
        "degraded": 1 if outcome == "degraded" else 0,
        "total": 1,
    }

    report: dict[str, Any] = {
        "schema_version": "st.report.v1",
        "ruleset_version": ruleset.get("ruleset_version", "neutralization-r1"),
        "operations": operations,
        "snapshots": [snapshot],
        "curves": curves,
        "reactions": reactions,
        "sources": sources,
        "outcome_summary": summary,
    }
    report["report_id"] = hashlib.sha256(_canonical(report).encode("utf-8")).hexdigest()[:16]
    return report
