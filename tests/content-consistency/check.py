#!/usr/bin/env python3
"""UI-事实层一致性门禁：把「试剂架上每个瓶装试剂都在事实层可玩且有浓度」变成机器判定。

008 起试剂架由物化 ruleset 的 `reagent_solution` 字段驱动——玩家实际能取用的瓶装试剂
集合 = ruleset 中带 reagent_solution 的可玩物质。每个都必须：可玩(playable=true)、
浓度>0、来源锚定（非硬编码冒充、非求解结果）。同时反向保证前端不再硬编码 REAGENTS
浓度表（旧范式病根）。

判定规则（正向即通过）：
1. ruleset 中每个带 reagent_solution 的 compound：playable=true、concentration_mol_L>0、
   source 非空；hazard/solvent 标记合法。
2. 前端 web-ui 源码不得再硬编码 `REAGENTS` 浓度表（正则扫描 `compound_id.*concentration_mol_L.*0.` 旧表模式）；
   试剂架须由 /api 从 ruleset 派生。
3. 至少 1 个瓶装试剂（防门禁空跑）。

用法：python3 tests/content-consistency/check.py [repo_root]
依赖：仅标准库。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

errors: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"[content-consistency] FAIL {msg}", file=sys.stderr)


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "AGENTS.md").is_file() and (candidate / "content").is_dir():
            return candidate
    return start


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else find_root(Path(__file__).resolve().parent)
    ruleset_path = root / "content" / "materialized" / "ruleset.json"
    ui_src = root / "packages" / "web-ui" / "src"

    for path in (ruleset_path, ui_src):
        if not path.exists():
            fail(f"缺失 {path.relative_to(root)}")
    if errors:
        return 1

    ruleset = json.loads(ruleset_path.read_text(encoding="utf-8"))
    compounds = {c["compound_id"]: c for c in ruleset.get("compounds", [])}

    reagents = {cid: c for cid, c in compounds.items() if "reagent_solution" in c}
    if not reagents:
        fail("ruleset 无任何 reagent_solution 瓶装试剂（试剂架会空）")
        return 1

    for cid, c in sorted(reagents.items()):
        rs = c["reagent_solution"]
        if not c.get("playable"):
            fail(f"瓶装试剂「{cid}」playable=false（玩家取用会得到空结果）")
        conc = rs.get("concentration_mol_L")
        if not isinstance(conc, (int, float)) or conc <= 0:
            fail(f"瓶装试剂「{cid}」浓度非法（{conc}），须 >0")
        if not isinstance(rs.get("source"), str) or not rs["source"].strip():
            fail(f"瓶装试剂「{cid}」浓度无来源锚定")
        for flag in ("hazard", "solvent"):
            if flag in rs and not isinstance(rs[flag], bool):
                fail(f"瓶装试剂「{cid}」{flag} 标记非布尔值")

    # 反向：playable 但无可瓶装浓度的物质只备案（可经求解但不上架）
    for cid in sorted(set(compounds) - set(reagents)):
        if compounds[cid].get("playable"):
            notes.append(cid)

    # 前端不得硬编码旧 REAGENTS 浓度表（008 起由 /api 从 ruleset 派生）
    for p in ui_src.rglob("*"):
        if p.is_file() and p.suffix in {".ts", ".tsx"}:
            text = p.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"export\s+const\s+REAGENTS\b", text):
                fail(f"{p.relative_to(root)} 仍硬编码 REAGENTS 浓度表（应由 ruleset 派生）")
            if re.search(r"compound_id\s*:\s*[\"'][a-z_]+\[""].{0,80}concentration_mol_L\s*:\s*0\.", text):
                fail(f"{p.relative_to(root)} 疑似硬编码瓶装浓度（范式红线）")

    if errors:
        print(f"[content-consistency] 失败 {len(errors)} 项", file=sys.stderr)
        return 1
    print(f"[content-consistency] 通过：试剂架 {len(reagents)} 种瓶装试剂全部可玩+浓度>0+来源锚定：{sorted(reagents)}")
    if notes:
        print(f"[content-consistency] NOTE 事实层可玩但非瓶装上架（可经求解）：{notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
