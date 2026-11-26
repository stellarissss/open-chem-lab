#!/usr/bin/env python3
"""美术资产署名与存在性门禁：把「每个 SVG 逐资产署名 + 路径闭合 + LPPL 输出物约束」变成机器判定。

兑现 asset-pipeline README 第 5 步「跑 asset-attribution」与 ASSETS.csv「CI 会校验覆盖」的承诺。

判定规则（全部为正向即通过）：
1. assets/apparatus/*.svg 每个都在 ASSETS.csv 有署名行（used_in = apparatus/<stem>）。
2. ASSETS.csv 每条 apparatus 行的 SVG 文件真实存在（无孤儿署名）。
3. license 在白名单内（AGPL / GPLv2-only 等严格禁止）。
4. apparatus 卡的 asset 字段路径存在，且指向的 SVG 有署名行（事实层引用闭合）。
5. SVG 为纯 <path>、零 <text>（LPPL 只转译 pdflatex→pdftocairo 编译输出物）。
6. modified=yes 的行必须在 attribution_text 说明派生自哪些宏（禁止无据修改声明）。

用法：python3 tests/asset-attribution/check.py [repo_root]
依赖：仅标准库。
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

LICENSE_WHITELIST = {
    "MIT", "BSD-3-Clause", "Apache-2.0", "ISC", "CC0-1.0",
    "CC-BY-4.0", "CC-BY-3.0", "LPPL-1.3c (generated output only)",
}

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"[asset-attribution] FAIL {msg}", file=sys.stderr)


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
    assets_dir = root / "assets" / "apparatus"
    csv_path = root / "assets" / "attribution" / "ASSETS.csv"

    if not csv_path.is_file():
        fail(f"缺少署名表 {csv_path}")
        return 1

    # 读 CSV（跳过 # 注释行）
    rows: list[dict[str, str]] = []
    with csv_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(line for line in fh if not line.lstrip().startswith("#"))
        for row in reader:
            rows.append(row)

    # used_in -> 署名行（apparatus/* 才纳入本门禁）
    by_used_in: dict[str, dict[str, str]] = {}
    for row in rows:
        used = (row.get("used_in") or "").strip()
        if used.startswith("apparatus/"):
            if used in by_used_in:
                fail(f"重复署名 used_in={used}")
            by_used_in[used] = row
            if (row.get("license") or "").strip() not in LICENSE_WHITELIST:
                fail(f"{used}: license 不在白名单：{row.get('license')!r}")
            if (row.get("modified") or "").strip() == "yes":
                attr = (row.get("attribution_text") or "")
                if "macro" not in attr.lower() and "\\tkz" not in attr:
                    fail(f"{used}: modified=yes 但 attribution_text 未说明派生宏")

    # 规则 1+5：每个 SVG 有署名 + 纯 path 无 text
    svgs = sorted(assets_dir.glob("*.svg")) if assets_dir.is_dir() else []
    if not svgs:
        fail(f"assets/apparatus/ 下无 SVG")
    for svg in svgs:
        used = f"apparatus/{svg.stem}"
        if used not in by_used_in:
            fail(f"{svg.name} 未在 ASSETS.csv 署名（缺 used_in={used}）")
        text = svg.read_text(encoding="utf-8")
        if re.search(r"<text[\s>]", text):
            fail(f"{svg.name} 含 <text>，非纯 path 编译输出物（需转曲）")

    # 规则 2：无孤儿署名（CSV 的 apparatus 行对应文件存在）
    for used in by_used_in:
        target = root / "assets" / f"{used}.svg"
        if not target.is_file():
            fail(f"署名行 used_in={used} 对应文件不存在：{target}")

    # 规则 4：apparatus 卡 asset 路径存在 + 有署名
    cards = sorted((root / "content" / "rules").rglob("apparatus/*.json"))
    for card in cards:
        data = json.loads(card.read_text(encoding="utf-8"))
        asset = data.get("asset")
        if not asset:
            fail(f"{card.name}: 缺 asset 字段")
            continue
        target = root / asset
        if not target.is_file():
            fail(f"{card.name}: asset 指向不存在的文件 {asset}")
            continue
        used = f"apparatus/{target.stem}"
        if used not in by_used_in:
            fail(f"{card.name}: asset={asset} 对应 SVG 无署名（缺 used_in={used}）")

    if errors:
        print(f"[asset-attribution] 失败：{len(errors)} 项", file=sys.stderr)
        return 1
    print(f"[asset-attribution] 通过：{len(svgs)} 个 SVG 全部署名、许可合规、纯 path、路径闭合（{len(cards)} 张器材卡）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
