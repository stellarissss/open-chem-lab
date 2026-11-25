#!/usr/bin/env python3
"""构建期物化链：把 content/rules/** 的分散 YAML/JSON 物化为单一 ruleset。

- 输入：content/rules/ 下按体系分目录的 compound/rule JSON（人工精校、可 diff/回滚）
- 输出：content/materialized/ruleset.json（内容寻址、版本化、运行时加载、零网络依赖）
- 参数变更须改 source 文件的 rule_revision，物化产物随之更新，禁原地覆盖。

用法：python3 tools/materialize-rules.py [repo_root]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    rules_dir = root / "content" / "rules"
    compounds: list[dict] = []
    apparatus: list[dict] = []
    rules: list[dict] = []
    systems: set[str] = set()

    for path in sorted(rules_dir.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "compounds" in path.parts:
            compounds.append(data)
        elif "apparatus" in path.parts:
            # 器材参数单一事实源（spec-005 装置建造）：驱动实验台容量/物理约束。
            apparatus.append(data)
        elif "rules" in path.parts:
            rules.append(data)
            if data.get("system"):
                systems.add(data["system"])

    payload = {
        "schema_version": "st.ruleset.v1",
        "ruleset_version": "neutralization-r1",
        "systems": sorted(systems),
        "compounds": sorted(compounds, key=lambda c: c["compound_id"]),
        "apparatus": sorted(apparatus, key=lambda a: a["apparatus_id"]),
        "reaction_rules": sorted(rules, key=lambda r: r["rule_id"]),
    }
    body = canonical(payload)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    payload["ruleset_sha256"] = digest

    out = root / "content" / "materialized"
    out.mkdir(parents=True, exist_ok=True)
    (out / "ruleset.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[materialize] {len(compounds)} compounds, {len(apparatus)} apparatus, {len(rules)} rules, {len(systems)} systems")
    print(f"[materialize] ruleset_sha256={digest}")
    print(f"[materialize] -> {out / 'ruleset.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
