#!/usr/bin/env python3
"""证据自证门禁：把「测试声称的依赖真被调用、期望值有独立来源」变成可机器判定的检查。

针对的失效模式（来自切片 003/004 复盘）：
- 测试函数名/验收文字声称用 chempy 对拍，实际是硬编码解析公式，全程未 import。
- 黄金用例期望值由被测引擎自己生成，形成自证循环却标「数值零错」。

本脚本静态校验（配合 golden runner 的运行时指纹与 CI grep）：
1. cases.json 每条期望标注 source ∈ {authority_snapshot, independent_crosscheck, analytic}；
2. evidence.crosscheck_tools 声明的工具，在 runner 源码中确有真实 import；
3. 每个 independent_crosscheck 用例被声明的工具覆盖，且每个覆盖用例确属该来源类型；
4. authority_snapshot 用例的签核记录文件存在（体系级签核链）；
5. cases.json 的 database_sha256 与签核记录中的权威源哈希一致（期望值锚定权威源）。

用法：python3 tests/evidence-check/check.py [repo_root]
依赖：仅标准库。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VALID_SOURCES = {"authority_snapshot", "independent_crosscheck", "analytic"}
# 允许在 spec / runner 中作为「对拍工具」出现的库白名单；声明即须真实 import。
KNOWN_TOOLS = {"chempy", "phreeqpython", "cantera", "reaktoro"}

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"[evidence] FAIL {msg}", file=sys.stderr)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"无法解析 {path}: {exc}")
        return None


def has_real_import(source: str, tool: str) -> bool:
    """源码中确有 import 语句（排除纯注释/字符串提及）。"""
    pattern = re.compile(
        rf"^\s*(?:from\s+{re.escape(tool)}\b|import\s+{re.escape(tool)}\b)",
        re.MULTILINE,
    )
    return bool(pattern.search(source))


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
    cases_path = root / "content" / "golden-cases" / "neutralization" / "cases.json"
    runner_path = root / "tests" / "golden-cases" / "run.py"
    print(f"[evidence] root: {root}")

    data = load_json(cases_path)
    if data is None:
        return 2
    runner = runner_path.read_text(encoding="utf-8")

    # 1. 每条期望必须标注来源
    all_cases = list(data.get("cases", [])) + list(data.get("hazard_cases", []))
    sources: dict[str, str] = {}
    for case in all_cases:
        cid = case["case_id"]
        exp = case.get("expect", {})
        src = exp.get("source")
        if src not in VALID_SOURCES:
            fail(f"{cid}: expect.source={src!r} 非合法来源 {sorted(VALID_SOURCES)}")
        else:
            sources[cid] = src
    print(f"[evidence] 来源标注 {len(sources)}/{len(all_cases)} 条齐全")

    # 2/3. 声明的对拍工具须真 import，且覆盖关系与来源标注自洽
    evidence = data.get("evidence", {})
    tools = evidence.get("crosscheck_tools", [])
    if not tools:
        fail("evidence.crosscheck_tools 为空：缺少独立对拍声明")
    covered: set[str] = set()
    for tool in tools:
        name = tool.get("name", "")
        if name not in KNOWN_TOOLS:
            fail(f"未登记的对拍工具 {name!r}（白名单 {sorted(KNOWN_TOOLS)}）")
            continue
        if not has_real_import(runner, name):
            fail(f"对拍工具 {name} 被声明但 runner 无真实 import（疑似硬编码冒充）")
        else:
            print(f"[evidence] 工具 {name} 在 runner 中有真实 import")
        for cid in tool.get("covers", []):
            if sources.get(cid) != "independent_crosscheck":
                fail(f"{cid}: 被 {name} 覆盖但 expect.source={sources.get(cid)!r}（应为 independent_crosscheck）")
            covered.add(cid)

    for cid, src in sources.items():
        if src == "independent_crosscheck" and cid not in covered:
            fail(f"{cid}: 标为 independent_crosscheck 但无对拍工具覆盖（独立来源未兑现）")

    # 4. 权威快照来源须有签核记录
    sign_path = root / str(data.get("source", ""))
    authority = [cid for cid, s in sources.items() if s == "authority_snapshot"]
    if authority and not sign_path.is_file():
        fail(f"存在 {len(authority)} 条 authority_snapshot 用例但签核记录不存在：{sign_path}")
    else:
        print(f"[evidence] 权威快照来源 {len(authority)} 条，签核记录存在")

    # 5. 期望锚定的权威源哈希须与签核记录中同库快照一致
    if sign_path.is_file():
        record = load_json(sign_path)
        if record:
            database = data.get("database")
            rec_hash = next(
                (s.get("sha256") for s in record.get("authoritative_sources", [])
                 if s.get("snapshot_file") == database),
                None,
            )
            case_hash = data.get("database_sha256")
            if not rec_hash:
                fail(f"签核记录中找不到 {database} 的 sha256")
            elif case_hash and rec_hash != case_hash:
                fail(f"权威源哈希不一致：cases.json={case_hash} 签核记录={rec_hash}")
            else:
                print("[evidence] 期望锚定的权威源哈希与签核记录一致")

    if errors:
        print(f"[evidence] 失败 {len(errors)} 项", file=sys.stderr)
        return 1
    print("[evidence] 通过：依赖真实调用声明、期望来源齐全、独立对拍覆盖、签核链闭合")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
