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
import re
import sys
from collections import Counter, defaultdict
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


def guard_apparatus(data: dict, path: Path) -> None:
    """器材护栏：apparatus_id 小写 snake_case 且与文件名一致；id 唯一由 collect 层保证。"""
    aid = data.get("apparatus_id", "")
    if not re.fullmatch(r"[a-z0-9_]+", aid):
        fail(f"护栏拒绝 {path.name}: apparatus_id 须小写 snake_case，实际 {aid!r}")
    if aid != path.stem:
        fail(f"护栏拒绝 {path.name}: apparatus_id={aid!r} 与文件名 {path.stem!r} 不一致")
    conf = data.get("confidence", {}).get("level")
    review = data.get("review", {}).get("status")
    if conf == "ml_guess":
        fail(f"护栏拒绝 {path.name}: confidence=ml_guess 禁用")
    if conf == "verified" and review != "signed_off":
        fail(f"护栏拒绝 {path.name}: verified 器材须 signed_off")
    if data.get("rule_revision", 0) < 1:
        fail(f"护栏拒绝 {path.name}: rule_revision 须 >=1")
    if data.get("capacity_mL", 0) <= 0:
        fail(f"护栏拒绝 {path.name}: capacity_mL 须 > 0")
    grads = data.get("graduations", [])
    if any(g > data["capacity_mL"] for g in grads):
        fail(f"护栏拒绝 {path.name}: 刻度值超出容量")


ELEMENT_RE = re.compile(r"([A-Z][a-z]?)(\d*)")


def parse_formula(formula: str) -> Counter:
    """把简式解析为元素计数（如 CH3COOH -> C2 H4 O2, NH3·H2O -> N1 H5 O1）。

    支持点号水合物、括号按最外层展开不了的简单式；解析不了的返回空计数并由调用方跳过。
    这是计量守恒的元素计数校验，避免引入 RDKit 重依赖。
    """
    counts: Counter = Counter()
    # 点号分段（水合物/加合物），逐段解析后累加
    for part in formula.split("·"):
        for elem, num in ELEMENT_RE.findall(part):
            counts[elem] += int(num) if num else 1
    return counts


def element_balance(rxn: dict) -> tuple[Counter, Counter] | None:
    """从 reaction 的 reactants/products 计数映射 + 可选 formula 映射算元素守恒。

    reactants/products 的键是物种 ID；若物种 ID 本身是化学式（如 H+ / OH- / H2O），
    去掉电荷上标后解析。带下标数字的键按化学式处理；纯自定义 ID 无法解析则返回 None。
    """
    def side(mapping: dict) -> Counter | None:
        total: Counter = Counter()
        for species, coeff in mapping.items():
            base = species.split("+")[0].split("-")[0].strip()
            parsed = parse_formula(base)
            if not parsed:
                return None
            for elem, count in parsed.items():
                total[elem] += count * coeff
        return total

    left, right = side(rxn.get("reactants", {})), side(rxn.get("products", {}))
    if left is None or right is None:
        return None
    return left, right


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

    # 元素守恒：反应前后各元素原子数相等（轻量解析，不依赖 RDKit）
    balance = element_balance(rxn)
    if balance is not None:
        left, right = balance
        if left != right:
            fail(
                f"元素守恒失败 {path.name}: "
                f"反应物 {dict(left)} != 产物 {dict(right)}"
            )

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
        # 由目录判断类型：compounds/ 下为 compound，apparatus/ 下为 apparatus，
        # rules/ 下为 reaction_rule（注意 apparatus 判断须在 rules 之前，二者同属 rules/ 子树）。
        if "compounds" in path.parts:
            kind = "compound"
        elif "apparatus" in path.parts:
            kind = "apparatus"
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
        elif kind == "apparatus":
            guard_apparatus(data, path)
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
