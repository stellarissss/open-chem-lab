#!/usr/bin/env python3
"""依赖许可证白名单门禁（spec-001 雏形）。

红线（见 01-Architecture.md 第七节）：
- 白名单：MIT / BSD / Apache-2.0 / ISC / CC0 / CC-BY / LGPL-2.1 / LGPL-3.0 / Unlicense / 0BSD / Python-2.0 等宽松许可
- 禁止：AGPL / GPLv2-only / SSPL / BUSL 等传染性或源可用许可
- 复杂 SPDX 表达式（含 OR/AND、带异常）：人工复核，默认告警不阻断（避免误杀双许可）

用法：在仓库根执行 `python3 tests/license-scan/scan.py`。
数据源：pnpm licenses list --json（仅扫描 JS 侧；Python/Rust 侧在各自接入切片补扫）。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict

# 宽松 / 兼容 LGPL-3.0 主链的许可（规范化小写比较）
ALLOW = {
    "mit", "isc", "apache-2.0", "apache-2", "bsd-2-clause", "bsd-3-clause",
    "bsd-4-clause", "0bsd", "cc0-1.0", "cc0", "unlicense", "python-2.0",
    "psf-2.0", "zlib", "libpng", "mpl-2.0", "wtfpl", "lgpl-2.1", "lgpl-2.1-or-later",
    "lgpl-3.0", "lgpl-3.0-only", "lgpl-3.0-or-later", "cc-by-4.0", "cc-by-3.0",
}
# 严格禁止（传染性 / 源可用 / 商业限制）
DENY = {
    "agpl-3.0", "agpl-3.0-only", "agpl-3.0-or-later", "agpl-1.0", "agpl-1.0-only",
    "gpl-2.0", "gpl-2.0-only", "gplv2-only", "gpl-3.0-only", "sspl-1.0",
    "busl-1.1", "elastic-2.0", "cc-by-nc", "cc-by-nc-sa",
}
# 复杂表达式（OR/AND/WITH）先告警，不自动阻断
COMPLEX_RE = re.compile(r"\b(OR|AND|WITH)\b")


def normalize(lic: str) -> str:
    s = str(lic).strip().lower()
    s = s.replace("license", "").strip()
    return s


def main() -> int:
    try:
        out = subprocess.run(
            ["pnpm", "licenses", "list", "--json"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"[license-scan] 无法获取依赖许可证：{exc}", file=sys.stderr)
        return 2

    data = json.loads(out)
    by_license: dict[str, list[str]] = defaultdict(list)
    for lic, entries in data.items():
        for e in entries:
            by_license[str(lic)].append(e.get("name", "?"))

    denied: list[tuple[str, str]] = []
    warned: list[tuple[str, str]] = []
    for lic, names in by_license.items():
        norm = normalize(lic)
        if norm in ALLOW or norm in {"unknown", "none", ""} and len(names) == 0:
            continue
        if any(tag in norm for tag in ("agpl", "gpl-2.0", "gplv2", "sspl", "busl", "elastic")) or norm in DENY:
            for n in names:
                denied.append((lic, n))
        elif COMPLEX_RE.search(lic) or norm not in ALLOW:
            for n in names:
                warned.append((lic, n))

    total = sum(len(v) for v in by_license.values())
    print(f"[license-scan] 扫描 {total} 个依赖，{len(by_license)} 种许可证声明")
    if warned:
        print(f"[license-scan] 告警 {len(warned)} 项（复杂/未知许可，需人工复核，不阻断）：")
        for lic, name in sorted(warned)[:30]:
            print(f"  ? {name}: {lic}")
    if denied:
        print(f"[license-scan] 失败 {len(denied)} 项（禁止许可）：", file=sys.stderr)
        for lic, name in sorted(denied):
            print(f"  X {name}: {lic}", file=sys.stderr)
        return 1
    print("[license-scan] 通过：无 AGPL / GPLv2-only / 源可用许可")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
