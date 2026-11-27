#!/usr/bin/env python3
"""M1 全链路集成验收（spec-007）：经 gateway 连续走通一条垂直切片。

覆盖 001–006 串联后的五个环节与四类好玩载体，并用测试产物承载证据：

- 全链路：health → speciation → phenomena → timeline（含缓存复用）→ report，
  全程只访问 gateway 的 /api/v1/*，不直连 solver（01 第六节依赖规则）。
- 载体①错误操作后果（003）：水入酸 / 酸入水温升数值相同，splash 指令仅水入酸派生。
- 载体②装置建造最小版（005）：取器材 + 倾倒的操作序列进入报告 operations。
- 载体③物种面板与时间轴回放（004）：关键帧物种快照与同配比单容器求解同源。
- 载体④实验报告（006）：报告快照 pH / 离子强度 / 物种浓度与求解出口逐字段一致，
  曲线与时间轴产物一致，三态出口如实，source_ref 引用闭合，report_id 幂等。
- 静态护栏：web-ui 源码不直连求解库（无 solver 端口 / 直连 import）。

纯标准库，不需要 docker build；CI 与本地均可跑。启动 gateway(tsx) 与 solver-worker
两个子进程，用固定高端口避免与默认端口冲突，退出时确保回收。
"""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VENV_PY = ROOT / "packages/solver-worker/.venv/bin/python"
BUNDLE_VENV = Path("/root/.config/open-chem-lab/solver-venv/bin/python")
SOLVER_PORT = 18768
GATEWAY_PORT = 3004
SOLVER = f"http://127.0.0.1:{SOLVER_PORT}"
GATEWAY = f"http://127.0.0.1:{GATEWAY_PORT}"


def python_bin() -> str:
    if VENV_PY.exists():
        return str(VENV_PY)
    if BUNDLE_VENV.exists():
        return str(BUNDLE_VENV)
    return sys.executable


def free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def wait_health(url: str, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False


def http_json(method: str, url: str, body: dict[str, Any] | None = None,
              timeout: float = 10.0) -> tuple[dict[str, Any], dict[str, str]]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"content-type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.loads(r.read())
        headers = {k.lower(): v for k, v in r.headers.items()}
        return payload, headers


def eq(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    eq(free(SOLVER_PORT) and free(GATEWAY_PORT),
       f"端口 {SOLVER_PORT}/{GATEWAY_PORT} 被占用，无法启动全链路测试")

    env_solver = dict(os.environ, PYTHONPATH=str(ROOT / "packages/solver-worker/src"),
                      ST_REPO_ROOT=str(ROOT), HOST="127.0.0.1")
    solver_proc = subprocess.Popen(
        [python_bin(), "-m", "st_solver_worker", "--http", "--port", str(SOLVER_PORT)],
        cwd=ROOT, env=env_solver, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    gw_dir = ROOT / "packages/gateway"
    tsx = gw_dir / "node_modules/.bin/tsx"
    env_gw = dict(os.environ, PORT=str(GATEWAY_PORT), HOST="127.0.0.1",
                  SOLVER_URL=SOLVER)
    gw_proc = subprocess.Popen(
        [str(tsx), "src/index.ts"], cwd=gw_dir, env=env_gw,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        eq(wait_health(SOLVER + "/health"), "[链路] solver /health 不可达")
        eq(wait_health(GATEWAY + "/api/v1/health"), "[链路] gateway /api/v1/health 不可达")
        print("[pipeline] OK health: solver + gateway 均可达")

        # ---- 环节 1：单容器求解（经 gateway，携带协议版本头）----
        acid = {"container_id": "b1", "substances": [
            {"compound_id": "hcl", "concentration_mol_L": 0.1, "volume_L": 1.0}]}
        spec, h = http_json("POST", GATEWAY + "/api/v1/speciation", acid)
        eq(h.get("x-protocol") == "st.solution_speciation.v1",
           f"[链路] speciation 协议头缺失: {h.get('x-protocol')}")
        eq(spec["outcome"] == "solved" and 1.0 < spec["ph"] < 1.2,
           f"[数值] 单容器求解异常: {spec['outcome']} ph={spec['ph']}")
        print(f"[pipeline] OK 求解: outcome={spec['outcome']} ph={spec['ph']:.4f} "
              f"(x-protocol={h['x-protocol']})")

        # ---- 环节 2：现象派生（经 gateway，指示剂 H-H 连续混色）----
        phbody = {"container_id": "p1", "substances": [
            {"compound_id": "naoh", "concentration_mol_L": 0.1, "volume_L": 1.0},
            {"compound_id": "phenolphthalein", "concentration_mol_L": 0.001, "volume_L": 0.01}]}
        directives, _ = http_json("POST", GATEWAY + "/api/v1/speciation/phenomena", phbody)
        color = [d for d in directives if d["type"] == "color_change"]
        eq(len(color) == 1 and color[0]["trigger"]["derivation"] == "henderson_hasselbalch",
           "[载体③] 指示剂现象未按 H-H 派生")
        eq(0.0 < color[0]["intensity"] <= 1.0, "[数值] 指示剂混色分数越界")
        ph2, _ = http_json("POST", GATEWAY + "/api/v1/speciation", phbody)
        expect_ratio = 10 ** (ph2["ph"] - color[0]["physics"]["pka"])
        eq(abs(color[0]["physics"]["indicator_ratio"] / expect_ratio - 1) < 1e-4,
           "[数值] 派生现象 indicator_ratio 与求解 pH 不一致")
        print(f"[pipeline] OK 现象: 酚酞 color_change intensity={color[0]['intensity']:.4f} "
              f"(H-H 派生，回指求解 pH={ph2['ph']:.4f})")

        # ---- 环节 3：时间轴回放 + 网关缓存复用 ----
        tl, h = http_json("GET", GATEWAY + "/api/v1/timeline?system=strong")
        eq(h.get("x-protocol") == "st.timeline.v1" and h.get("x-cache") == "miss",
           "[链路] 时间轴首次请求未 miss 或缺协议头")
        eq(len(tl["keyframes"]) == 9 and int(h["x-solve-calls"]) == 9,
           "[链路] 时间轴关键帧数与求解调用数不一致")
        tl2, h2 = http_json("GET", GATEWAY + "/api/v1/timeline?system=strong")
        eq(h2.get("x-cache") == "hit" and h2.get("x-solve-calls") == "0"
           and tl2["timeline_id"] == tl["timeline_id"],
           "[链路] 时间轴二次请求未命中缓存或 id 漂移")
        # 载体③：关键帧物种快照与同配比单容器求解同源（逐字段）
        anchor = tl["keyframes"][0]["speciation"]
        solo = dict(acid)
        solo["container_id"] = tl["keyframes"][0]["container_id"]
        solo_spec, _ = http_json("POST", GATEWAY + "/api/v1/speciation", solo)
        eq(anchor["ph"] == solo_spec["ph"]
           and anchor["ionic_strength"] == solo_spec["ionic_strength"],
           "[载体③] 时间轴锚点 pH/离子强度与单容器求解不同源")
        print(f"[pipeline] OK 时间轴: {len(tl['keyframes'])} 帧, "
              f"缓存 miss(9 calls) → hit(0 calls), 锚点回指求解一致")

        # ---- 载体①：错误操作后果 —— 水入酸 / 酸入水温升同值、飞溅仅水入酸 ----
        hazard = [
            {"compound_id": "sulfuric_acid_conc", "concentration_mol_L": 18.4, "volume_L": 0.0544},
            {"compound_id": "water", "concentration_mol_L": 1.0, "volume_L": 1.0},
        ]
        wa, _ = http_json("POST", GATEWAY + "/api/v1/heat",
                          {"container_id": "hz", "addition_order": "water_into_acid", "substances": hazard})
        aw, _ = http_json("POST", GATEWAY + "/api/v1/heat",
                          {"container_id": "hz", "addition_order": "acid_into_water", "substances": hazard})
        eq(wa["outcome"] == aw["outcome"] == "solved", "[载体①] 稀释热解未成功")
        eq(wa["delta_T_K"] == aw["delta_T_K"],
           f"[数值] 两种加入顺序温升不同（ΔH 是状态函数）: {wa['delta_T_K']} vs {aw['delta_T_K']}")
        eq(wa["splash_risk"] is True and aw["splash_risk"] is False,
           "[载体①] 飞溅风险未按加入顺序派生")
        wa_types = {d["type"] for d in wa["directives"]}
        aw_types = {d["type"] for d in aw["directives"]}
        eq("splash" in wa_types and "splash" not in aw_types
           and "temperature_change" in wa_types and "temperature_change" in aw_types,
           f"[载体①] 飞溅/温升指令差异不成立: {wa_types} vs {aw_types}")
        print(f"[pipeline] OK 错误操作: 水入酸/酸入水 ΔT={wa['delta_T_K']:.4f}K 同值, "
              f"splash 仅水入酸 ({wa_types} vs {aw_types})")

        # ---- 环节 4 + 载体②④：报告（操作序列入库、数值零加工、引用闭合、三态、幂等）----
        ops = [
            {"seq": 1, "kind": "place_apparatus", "container_id": "b1", "apparatus_id": "beaker_250ml"},
            {"seq": 2, "kind": "pour", "container_id": "b1", "compound_id": "hcl",
             "concentration_mol_L": 0.1, "volume_L": 1.0},
        ]
        req = {"operations": ops, "substances": acid["substances"], "system": "strong",
               "container_id": "b1"}
        report, h = http_json("POST", GATEWAY + "/api/v1/report", req)
        eq(h.get("x-protocol") == "st.report.v1", "[链路] 报告协议头缺失")
        eq(len(report["operations"]) == 2 and report["operations"][0]["kind"] == "place_apparatus"
           and report["operations"][1]["kind"] == "pour",
           "[载体②] 取器材/倾倒操作序列未进入报告")
        snap = report["snapshots"][0]
        eq(snap["ph"] == spec["ph"] and snap["ionic_strength"] == spec["ionic_strength"],
           "[载体④] 报告 pH/离子强度被加工")
        rep_sp = {s["name"]: s["concentration_mol_l"] for s in snap["species"]}
        src_sp = {s["species_id"]: s["concentration_mol_L"] for s in spec["species"]}
        eq(rep_sp == src_sp, "[载体④] 报告物种浓度与求解出口不一致")
        eq([{"species": c["species"], "points": c["points"]} for c in report["curves"]]
           == [{"species": c["species"], "points": c["points"]} for c in tl["curves"]],
           "[载体④] 报告曲线与时间轴产物不一致")
        ids = {s["source_id"] for s in report["sources"]}
        refs = [snap["source_ref"]] + [s["source_ref"] for s in snap["species"]]
        refs += [c["source_ref"] for c in report["curves"]] + [r["source_ref"] for r in report["reactions"]]
        eq(all(r in ids for r in refs), f"[载体④] 悬空 source_ref: {[r for r in refs if r not in ids]}")
        again, _ = http_json("POST", GATEWAY + "/api/v1/report", req)
        eq(again["report_id"] == report["report_id"], "[载体④] report_id 不幂等")
        print(f"[pipeline] OK 报告: ops={len(report['operations'])} "
              f"数值零加工 / 引用闭合 / report_id={report['report_id']} 幂等")

        # ---- 三态出口如实：覆盖外物质 -> no_significant_change 且保留 reason ----
        degraded, _ = http_json("POST", GATEWAY + "/api/v1/speciation",
                                {"container_id": "x", "substances": [
                                    {"compound_id": "unknown_xyz", "concentration_mol_L": 0.1, "volume_L": 1}]})
        eq(degraded["outcome"] == "no_significant_change" and bool(degraded.get("reason")),
           "[红线] 覆盖外物质未如实降级")
        print(f"[pipeline] OK 三态出口: 覆盖外 → {degraded['outcome']} (reason 保留)")

        # ---- 静态护栏：web-ui 不直连求解库 ----
        ui_src = (ROOT / "packages/web-ui/src")
        offenders: list[str] = []
        for p in ui_src.rglob("*"):
            if p.is_file() and p.suffix in {".ts", ".tsx", ".js"}:
                text = p.read_text(encoding="utf-8", errors="ignore")
                if re.search(r"8765|localhost:\d{4}|127\.0\.0\.1:\d{4}", text) or \
                   re.search(r"from\s+['\"]st_solver_worker|import\s+phreeqpython", text):
                    offenders.append(str(p.relative_to(ROOT)))
        eq(not offenders, f"[依赖规则] web-ui 疑似直连求解库或硬编码求解端口: {offenders}")
        print("[pipeline] OK 依赖规则: web-ui 仅经 /api/v1/* 取数，无直连求解库")

        print("[pipeline] 通过：M1 全链路贯通 + 四类好玩载体证据 + 数值零错 + 三态如实")
        return 0
    except AssertionError as e:
        print(f"[pipeline] FAIL {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[pipeline] ERROR {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    finally:
        for proc in (gw_proc, solver_proc):
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
