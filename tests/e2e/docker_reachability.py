#!/usr/bin/env python3
"""容器部署可达验收（spec-007 验收标准 4）：对已 docker compose up 的服务做健康检查与全链路抽样。

前置：`docker compose -f deploy/docker-compose.minimal.yml up -d`（CI deploy-build job 已执行）。
验收：web 静态页可达、gateway/solver/postgres 健康、经网关的求解/报告/错误操作一致，
且报告来源锚点闭合（覆盖 solver-worker 容器内 golden-cases COPY 闭合）。纯标准库。
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

GATEWAY = os.environ.get("GATEWAY_URL", "http://127.0.0.1:3001")
WEB = os.environ.get("WEB_URL", "http://127.0.0.1:8080")


def request(method: str, url: str, body: dict[str, Any] | None = None) -> tuple[Any, int]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"content-type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read()) if r.headers.get("content-type", "").startswith("application/json") else r.read(), r.status


def main() -> int:
    try:
        # web 静态页
        _, code = request("GET", WEB + "/")
        assert code == 200, f"web 静态页 HTTP {code}"
        print("[docker] OK web 静态页 HTTP 200")

        # 网关健康
        health, code = request("GET", GATEWAY + "/api/v1/health")
        assert code == 200 and health["status"] == "ok", f"gateway health 异常: {health}"
        print(f"[docker] OK gateway health v{health['version']}")

        # 求解
        acid = {"container_id": "b1", "substances": [
            {"compound_id": "hcl", "concentration_mol_L": 0.1, "volume_L": 1.0}]}
        spec, _ = request("POST", GATEWAY + "/api/v1/speciation", acid)
        assert spec["outcome"] == "solved" and 1.0 < spec["ph"] < 1.2, f"求解异常: {spec}"
        print(f"[docker] OK 求解 ph={spec['ph']:.4f}")

        # 报告（覆盖容器内 golden-cases 来源锚点 COPY）
        report, _ = request("POST", GATEWAY + "/api/v1/report", {
            "operations": [{"seq": 1, "kind": "pour", "container_id": "b1",
                            "compound_id": "hcl", "concentration_mol_L": 0.1, "volume_L": 1.0}],
            "substances": acid["substances"], "system": "strong", "container_id": "b1"})
        snap = report["snapshots"][0]
        assert snap["ph"] == spec["ph"], "报告 pH 与求解不一致"
        ids = {s["source_id"] for s in report["sources"]}
        assert snap["source_ref"] in ids, "报告来源引用不闭合"
        print(f"[docker] OK 报告 id={report['report_id']} 数值零加工 / 来源闭合")

        # 错误操作后果
        hazard = [
            {"compound_id": "sulfuric_acid_conc", "concentration_mol_L": 18.4, "volume_L": 0.0544},
            {"compound_id": "water", "concentration_mol_L": 1.0, "volume_L": 1.0},
        ]
        wa, _ = request("POST", GATEWAY + "/api/v1/heat",
                        {"container_id": "h", "addition_order": "water_into_acid", "substances": hazard})
        aw, _ = request("POST", GATEWAY + "/api/v1/heat",
                        {"container_id": "h", "addition_order": "acid_into_water", "substances": hazard})
        assert wa["delta_T_K"] == aw["delta_T_K"] and wa["splash_risk"] and not aw["splash_risk"], \
            f"错误操作后果差异不成立: {wa['delta_T_K']}/{wa['splash_risk']} vs {aw['delta_T_K']}/{aw['splash_risk']}"
        print(f"[docker] OK 错误操作 ΔT={wa['delta_T_K']:.4f}K 同值 / splash 仅水入酸")

        print("[docker] 通过：容器起服 + 健康检查 + 网关全链路可达")
        return 0
    except Exception as e:
        print(f"[docker] FAIL {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
