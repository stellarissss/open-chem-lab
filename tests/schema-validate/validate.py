#!/usr/bin/env python3
"""内容层 schema 校验门禁（Python jsonschema，非 ajv）。

职责（spec-002 验收标准 2/3）：
- 校验 schemas/ 下各 JSON Schema 本身符合 draft 2020-12；
- 校验 content/rules/** 的数据文件对相应 schema 通过；
- 事实层护栏断言：
    * confidence=ml_guess → 拒绝（禁用）；
    * playable=true 须 review.status=signed_off 且 confidence=verified；
    * 非 verified 数据不得进入可玩层（compound.playable / rule 参与求解）；
    * 同一 reaction 反应物集合 + applicability.conditions 不得有两条 verified 规则（条件互斥）；
    * 反应计量守恒：net_charge_reactants == net_charge_products；
    * rule_revision 存在且 >= 1（参数变更可回滚）。

用法：python3 tests/schema-validate/validate.py [repo_root]
依赖：jsonschema（系统/venv 均已装 4.26.0，无新增依赖）。
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:
    print(f"[schema-validate] 缺少 jsonschema: {exc}", file=sys.stderr)
    raise SystemExit(2)

SCHEMA_MAP = {
    "compound": "compound.v1.schema.json",
    "apparatus": "apparatus.v1.schema.json",
    "reaction_rule": "reaction_rule.v1.schema.json",
    "solution_speciation": "solution_speciation.v1.schema.json",
}

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"无法解析 JSON {p}: {exc}")
        return None


def schema_for(root: Path, name: str):
    p = root / "schemas" / SCHEMA_MAP[name]
    data = load_json(p)
    if data is None:
        return None
    try:
        Draft202012Validator.check_schema(data)
    except Exception as exc:  # noqa: BLE001
        fail(f"schema 自身非法 {p.name}: {exc}")
        return None
    return Draft202012Validator(data)


def validate_instance(path: Path, validator, label: str) -> dict | None:
    data = load_json(path)
    if data is None:
        return None
    errs = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errs:
        for e in errs[:5]:
            fail(f"schema 校验失败 {label} @{list(e.path)}: {e.message}")
        if len(errs) > 5:
            fail(f"  ... 另有 {len(errs)-5} 处错误")
    return data


def guard_compound(data: dict, path: Path) -> None:
    conf = data.get("confidence", {}).get("level")
    review = data.get("review", {}).get("status")
    if conf == "ml_guess":
        fail(f"护栏拒绝 {path.name}: confidence=ml_guess 禁用")
    if data.get("playable") is True:
        if conf != "verified":
            fail(f"护栏拒绝 {path.name}: playable=true 但 confidence={conf}（须 verified）")
        if review != "signed_off":
            fail(f"护栏拒绝 {path.name}: playable=true 但 review.status={review}（须 signed_off）")
    if data.get("rule_revision", 0) < 1:
        fail(f"护栏拒绝 {path.name}: rule_revision 须 >=1")


def guard_rule(data: dict, path: Path, seen: dict) -> None:
    conf = data.get("confidence", {}).get("level")
    review = data.get("review", {}).get("status")
    if conf == "ml_guess":
        fail(f"护栏拒绝 {path.name}: confidence=ml_guess 禁用")
    if conf == "verified" and review != "signed_off":
        fail(f"护栏拒绝 {path.name}: verified 规则须 signed_off")
    if data.get("rule_revision", 0) < 1:
        fail(f"护栏拒绝 {path.name}: rule_revision 须 >=1")

    rxn = data.get("reaction", {})
    ncr, ncp = rxn.get("net_charge_reactants"), rxn.get("net_charge_products")
    if ncr is not None and ncp is not None and ncr != ncp:
        fail(f"计量守恒失败 {path.name}: 净电荷 {ncr} != {ncp}")

    if conf == "verified":
        key = (
            tuple(sorted(rxn.get("reactants", {}).keys())),
            tuple(sorted(data.get("applicability", {}).get("conditions", []))),
        )
        if key in seen:
            fail(f"条件互斥失败 {path.name}: 与 {seen[key]} 同反应物+同条件且均 verified")
        seen[key] = path.name


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
    print(f"[schema-validate] root: {root}")

    validators = {name: schema_for(root, name) for name in SCHEMA_MAP}
    if any(v is None for v in validators.values()):
        return 2

    rules_dir = root / "content" / "rules"
    checked = defaultdict(int)
    seen_rules: dict = {}

    for path in sorted(rules_dir.rglob("*.json")):
        rel = path.relative_to(root)
        # 由文件名前缀/目录判断类型：compounds/ 下为 compound，rules/ 下为 reaction_rule
        if "compounds" in path.parts:
            kind = "compound"
        elif "rules" in path.parts:
            kind = "reaction_rule"
        else:
            fail(f"无法判定类型: {rel}")
            continue
        data = validate_instance(path, validators[kind], str(rel))
        if data is None:
            continue
        checked[kind] += 1
        if kind == "compound":
            guard_compound(data, path)
        else:
            guard_rule(data, path, seen_rules)

    total = sum(checked.values())
    if not total:
        fail("未发现任何 content/rules/**/*.json 数据文件")
    print(f"[schema-validate] 校验 {total} 个数据文件：{dict(checked)}")

    if errors:
        print(f"[schema-validate] 失败 {len(errors)} 项：", file=sys.stderr)
        for e in errors:
            print(f"  X {e}", file=sys.stderr)
        return 1
    print("[schema-validate] 通过：schema 合法、数据合规、护栏齐全（verified/signed_off、无 ml_guess、条件互斥、计量守恒）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
