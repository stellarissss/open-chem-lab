#!/usr/bin/env python3
"""UI-事实层一致性门禁：把「前端可取的每个药品都在事实层可玩」变成机器判定。

根绝「蒸馏水可取但主求解判覆盖外」这类承诺—实现缝隙：web-ui 的 REAGENTS
是玩家能实际取用的药品集合，每一个 compound_id 都必须在物化 ruleset 里
以 playable=true 存在，否则玩家会对一个可操作的东西得到空结果。

判定规则（正向即通过）：
1. lab.ts 的 REAGENTS 每项 compound_id 出现在 ruleset.compounds[].compound_id。
2. 对应的 compound 卡 playable=true（非可玩卡不应出现在 UI 可取列表）。
3. 反向备案：ruleset 里的 playable 物质不必都在 UI（如 hno3/koh 可经求解但不出现在默认药品架）——输出 NOTE 不判失败。

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
    lab_ts = root / "packages" / "web-ui" / "src" / "lab.ts"
    ruleset_path = root / "content" / "materialized" / "ruleset.json"

    for path in (lab_ts, ruleset_path):
        if not path.is_file():
            fail(f"缺失 {path.relative_to(root)}")
    if errors:
        return 1

    # 提取 REAGENTS 数组里的 compound_id（只取该数组块，避免误抓其他字段）
    text = lab_ts.read_text(encoding="utf-8")
    m = re.search(r"export const REAGENTS[^=]*=\s*\[(.*?)\];", text, re.DOTALL)
    if not m:
        fail("lab.ts 未找到 REAGENTS 数组定义")
        return 1
    ui_ids = set(re.findall(r'compound_id:\s*["\']([^"\']+)["\']', m.group(1)))
    if not ui_ids:
        fail("REAGENTS 数组为空或未解析出 compound_id")
        return 1

    ruleset = json.loads(ruleset_path.read_text(encoding="utf-8"))
    compounds = {c["compound_id"]: c for c in ruleset.get("compounds", [])}
    playable = {cid for cid, c in compounds.items() if c.get("playable")}

    for cid in sorted(ui_ids):
        if cid not in compounds:
            fail(f"UI 可取「{cid}」不在 ruleset.compounds（玩家会得到空结果）")
        elif cid not in playable:
            fail(f"UI 可取「{cid}」在事实层 playable=false（不可玩）")

    for cid in sorted(playable - ui_ids):
        notes.append(cid)

    if errors:
        print(f"[content-consistency] 失败 {len(errors)} 项", file=sys.stderr)
        return 1
    print(f"[content-consistency] 通过：UI 可取 {len(ui_ids)} 种药品全部在事实层可玩：{sorted(ui_ids)}")
    if notes:
        print(f"[content-consistency] NOTE 事实层可玩但不在默认药品架：{notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
