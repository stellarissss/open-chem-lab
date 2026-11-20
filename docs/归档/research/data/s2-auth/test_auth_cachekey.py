#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权威源实测 3：内容寻址缓存键 + 构建期快照固化原型（阶段二 S3，不写产品代码）

目的：验证 E4 / E8「免计算 + 可复现分层」与「失效由数据快照/求解器/ruleset 三者版本驱动」——
  1. 内容寻址键 = 体系特征 + 条件哈希 + 求解器版本 + ruleset_version，验证确定性/区分性/雪崩；
  2. 构建期快照固化 = 端点/许可/快照日/校验和随产物分发，验证可审计与篡改检测；
  3. 失效语义 = 任一版本维度变化 → 键变化（缓存自动失效），无关维度变化 → 键不变。

用法：cd docs/research/data/s2-auth && python3 test_auth_cachekey.py
输出：auth_cachekey_result.json
"""
import json, os, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = "2026-11-16"


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def cache_key(system, conditions, solver_ver, ruleset_ver, key_len=16):
    """内容寻址键：体系特征 + 条件 + 求解器版本 + ruleset 版本的确定性哈希。"""
    payload = canonical({
        "system": system,
        "conditions": conditions,
        "solver_version": solver_ver,
        "ruleset_version": ruleset_ver,
    })
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:key_len]


def snapshot_record(endpoint, license_id, snapshot, payload_bytes):
    """构建期快照记录：溯源 + 许可 + 快照日 + 内容校验和。"""
    return {
        "endpoint": endpoint,
        "license": license_id,
        "snapshot_date": snapshot,
        "sha256": hashlib.sha256(payload_bytes).hexdigest(),
    }


def main():
    result = {
        "case": "auth_cachekey_and_snapshot_freeze",
        "snapshot": SNAPSHOT,
        "key_dimensions": ["system", "conditions", "solver_version", "ruleset_version"],
        "cases": [],
        "summary": {},
    }

    sys_ = {"species": ["HAc", "Ac-", "H+", "OH-"], "engine": "phreeqpython"}
    cond = {"T_C": 25.0, "pH_init": 4.76, "units": "mmol/kgw"}
    sv, rv = "phreeqpython-3.0.0", "ruleset-2026.11"

    k1 = cache_key(sys_, cond, sv, rv)
    k2 = cache_key(sys_, cond, sv, rv)  # 同输入
    # 无关维度：条件 dict 的键顺序变化（规范化后应等价）
    k3 = cache_key(sys_, {"units": "mmol/kgw", "pH_init": 4.76, "T_C": 25.0}, sv, rv)
    # 相关维度变化
    k_cond = cache_key(sys_, dict(cond, T_C=37.0), sv, rv)
    k_solver = cache_key(sys_, cond, "phreeqpython-3.1.0", rv)
    k_ruleset = cache_key(sys_, cond, sv, "ruleset-2026.12")

    result["cases"].append({
        "id": "deterministic_key",
        "expect": "同输入 → 同键（可复现命中）",
        "actual": {"k1": k1, "k2": k2}, "pass_": k1 == k2,
    })
    result["cases"].append({
        "id": "canonical_order_invariant",
        "expect": "条件键顺序无关（规范化序列化）→ 同键",
        "actual": {"k1": k1, "k_reordered": k3}, "pass_": k1 == k3,
    })
    result["cases"].append({
        "id": "invalidation_on_version_change",
        "expect": "solver/ruleset/条件任一变化 → 键变化（缓存自动失效）",
        "actual": {"base": k1, "cond": k_cond, "solver": k_solver, "ruleset": k_ruleset},
        "pass_": k1 != k_cond and k1 != k_solver and k1 != k_ruleset
                  and k_cond != k_solver != k_ruleset,
    })

    # 构建期快照固化 + 篡改检测
    payload = canonical({"log_k": 4.757, "source": "wateq4f_PWN.dat", "rxn": "HAc=H+ + Ac-"}).encode()
    snap = snapshot_record("pubchem.ncbi.nlm.nih.gov/rest/pug", "public-domain-USGS", SNAPSHOT, payload)
    snap2 = snapshot_record("pubchem.ncbi.nlm.nih.gov/rest/pug", "public-domain-USGS", SNAPSHOT, payload)
    tampered = snapshot_record("pubchem.ncbi.nlm.nih.gov/rest/pug", "public-domain-USGS", SNAPSHOT, payload + b"X")

    result["snapshot_record"] = snap
    result["cases"].append({
        "id": "snapshot_freeze_complete",
        "expect": "快照记录含 endpoint / license / snapshot_date / sha256 四要素",
        "actual": snap,
        "pass_": all(k in snap for k in ("endpoint", "license", "snapshot_date", "sha256"))
                  and len(snap["sha256"]) == 64,
    })
    result["cases"].append({
        "id": "tamper_detection",
        "expect": "内容变更 → sha256 变化（篡改可检出）；相同内容 → 校验和一致",
        "actual": {"ok": snap["sha256"], "recompute": snap2["sha256"], "tampered": tampered["sha256"]},
        "pass_": snap["sha256"] == snap2["sha256"] and snap["sha256"] != tampered["sha256"],
    })

    passed = sum(1 for c in result["cases"] if c["pass_"])
    total = len(result["cases"])
    result["summary"] = {
        "status": "PASS" if passed == total else "FAIL",
        "pass": passed, "total": total,
        "base_key": k1,
        "conclusion": "内容寻址键确定性/区分性/失效语义成立；快照四要素完整、篡改可检出；零新中间件（复用 solve_cache 结构）",
    }
    json.dump(result, open(os.path.join(HERE, "auth_cachekey_result.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"[{result['summary']['status']}] {passed}/{total}  base_key={k1}")


if __name__ == "__main__":
    main()
