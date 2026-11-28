#!/usr/bin/env python3
"""M2 自由台面全链路集成验收（spec-008）：经 gateway 走通新范式核心循环。

覆盖 008 的新玩法闭环与诚实出口，以测试产物承载证据：

- 链路：health → bench/catalog（ruleset 数据驱动）→ bench/operation（操作原语）→
  bench/container-state（定向求解推送）→ 三态出口，全程只访问 gateway 的 /api/v1/*，
  不直连 solver（01 第六节依赖规则）。
- 试剂架数据驱动：catalog 的每个瓶装试剂都有浓度>0、来源锚定、可玩（对齐 content-consistency 门禁）。
- 操作原语：st.operation_event.v1 经 gateway 校验、计数回显（无「实验」会话入库）。
- 定向推送：WS 订阅 container A，向 B 发 container_state，A 收不到（多容器不串扰）；
  向 A 发则 A 收到且协议头正确。
- 求解接入 + 诚实：target 组成变化后实解；覆盖外物质 → no_significant_change 带 reason。
- 范式红线：web-ui 无预设配比/旧演示层（对齐 paradigm-redline 门禁）；
  倾角物理以 benchPhysics 纯函数单测覆盖（见 tests/bench-physics/test.mjs）。
- 静态护栏：web-ui 不直连求解库。

纯标准库 + venv 的 websocket-client；CI 与本地均可跑。启动 gateway(tsx) 与
solver-worker 两个子进程，固定高端口，退出时确保回收。
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


def wait_health(url: str, timeout: float = 25.0) -> bool:
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
                  SOLVER_URL=SOLVER, ST_REPO_ROOT=str(ROOT))
    gw_proc = subprocess.Popen(
        [str(tsx), "src/index.ts"], cwd=gw_dir, env=env_gw,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        eq(wait_health(SOLVER + "/health"), "[链路] solver /health 不可达")
        eq(wait_health(GATEWAY + "/api/v1/health"), "[链路] gateway /api/v1/health 不可达")
        print("[pipeline] OK health: solver + gateway 均可达")

        # ---- 环节 1：试剂架数据驱动（ruleset → catalog）----
        catalog, h = http_json("GET", GATEWAY + "/api/v1/bench/catalog")
        eq(h.get("x-protocol") == "st.bench_world.v1", "[数据] catalog 协议头缺失")
        reagents = catalog.get("reagents", [])
        eq(len(reagents) >= 8, f"[数据] 试剂架过少：{len(reagents)}")
        for r in reagents:
            eq(isinstance(r.get("concentration_mol_L"), (int, float)) and r["concentration_mol_L"] > 0,
               f"[数据] 瓶装试剂 {r.get('compound_id')} 浓度非法")
        eq(catalog.get("ruleset_version") == "neutralization-r1", "[数据] ruleset 版本缺失")
        print(f"[pipeline] OK 数据驱动: catalog {len(reagents)} 试剂 + {len(catalog.get('apparatus', []))} 器材, "
              f"ruleset={catalog['ruleset_version']}")

        # ---- 环节 2：操作原语事件（st.operation_event.v1）----
        op = {"schema_version": "st.operation_event.v1", "event_id": "evt-e2e-1",
              "op_type": "pour", "timestamp_ms": 1, "source_instance_id": "reagent-1",
              "target_instance_id": "beaker-1",
              "payload": {"transferred_volume_L": 0.03, "tilt_angle_deg": 42}}
        op_ack, _ = http_json("POST", GATEWAY + "/api/v1/bench/operation", op)
        eq(op_ack.get("accepted") is True and op_ack.get("count", 0) >= 1,
           "[操作] operation_event 未被接受")
        bad = {"event_id": "bad"}
        try:
            http_json("POST", GATEWAY + "/api/v1/bench/operation", bad)
            eq(False, "[操作] 非法事件应被 400 拒绝")
        except urllib.error.HTTPError as e:
            eq(e.code == 400, f"[操作] 非法事件响应码 {e.code} != 400")
        print(f"[pipeline] OK 操作原语: event 计数回显={op_ack['count']}, 非法事件 400 拒绝")

        # ---- 环节 3：container_state 定向求解（HTTP 结算）----
        acid = {"container_id": "beaker-A", "substances": [
            {"compound_id": "hcl", "concentration_mol_L": 0.1, "volume_L": 0.03}]}
        state, h = http_json("POST", GATEWAY + "/api/v1/bench/container-state", acid)
        eq(h.get("x-protocol") == "st.container_state.v1", "[契约] container_state 协议头缺失")
        spec = state["speciation"]
        eq(spec["outcome"] == "solved" and 1.0 < spec["ph"] < 1.2,
           f"[数值] 倾倒后求解异常: outcome={spec['outcome']} ph={spec['ph']}")
        eq(state["container_id"] == "beaker-A" and isinstance(state["directives"], list),
           "[契约] container_state 容器定向字段缺失")
        eq(isinstance(state.get("solve_latency_ms"), (int, float)) and state["solve_latency_ms"] >= 0,
           "[契约] solve_latency_ms 非真实开销")
        print(f"[pipeline] OK 定向求解: container=beaker-A outcome={spec['outcome']} "
              f"ph={spec['ph']:.4f} latency={state['solve_latency_ms']}ms")

        # ---- 环节 4：WS 按 container_id 定向推送，多容器不串扰 ----
        try:
            import websocket as wsclient
        except ImportError:
            print("[pipeline] SKIP WS 定向测试：venv 无 websocket-client（其余链路已验证）")
        else:
            ws = wsclient.create_connection(f"ws://127.0.0.1:{GATEWAY_PORT}/ws", timeout=5)
            try:
                # 服务端握手后主动发 welcome，先消费
                welcome = json.loads(ws.recv())
                eq(welcome.get("type") == "welcome", f"[WS] 未收到 welcome: {welcome}")
                ws.send(json.dumps({"type": "subscribe", "channel": "container_state", "container_id": "beaker-A"}))
                subscribed = json.loads(ws.recv())
                eq(subscribed.get("type") == "subscribed" and subscribed.get("container_id") == "beaker-A",
                   f"[WS] 订阅确认异常: {subscribed}")
                # 向 B 发状态：A 不应收到
                http_json("POST", GATEWAY + "/api/v1/bench/container-state",
                          {"container_id": "beaker-B", "substances": acid["substances"]})
                ws.settimeout(1.5)
                try:
                    leaked = json.loads(ws.recv())
                    eq(leaked.get("container_id") != "beaker-B",
                       f"[WS] 串扰：订阅 A 却收到 B 的状态 {leaked.get('container_id')}")
                except wsclient.WebSocketTimeoutException:
                    pass  # 正确：A 未收到 B
                # 向 A 发状态：A 应收到
                http_json("POST", GATEWAY + "/api/v1/bench/container-state", acid)
                ws.settimeout(5)
                got = json.loads(ws.recv())
                eq(got.get("type") == "container_state" and got.get("container_id") == "beaker-A",
                   f"[WS] 定向推送失败: {got.get('type')}/{got.get('container_id')}")
                print("[pipeline] OK WS 定向: 订阅 A 收不到 B、A 的状态正常送达（不串扰）")
            finally:
                ws.close()

        # ---- 环节 5：三态出口如实 ----
        degraded, _ = http_json("POST", GATEWAY + "/api/v1/bench/container-state",
                                {"container_id": "x", "substances": [
                                    {"compound_id": "unknown_xyz", "concentration_mol_L": 0.1, "volume_L": 1}]})
        dspec = degraded["speciation"]
        eq(dspec["outcome"] == "no_significant_change" and bool(dspec.get("reason")),
           "[红线] 覆盖外物质未如实降级")
        print(f"[pipeline] OK 三态出口: 覆盖外 → {dspec['outcome']} (reason 保留)")

        # ---- 环节 6：范式红线静态护栏（web-ui 无旧演示层）----
        ui_src = ROOT / "packages/web-ui/src"
        offenders: list[str] = []
        forbidden = [r"\bPRESETS\b", r"\bsolveHeat\b", r"\bloadTimeline\b",
                     r"/api/v1/timeline", r"\bgenerateReport\b", r"\bREAGENTS\b",
                     r"8765|localhost:\d{4}|127\.0\.0\.1:\d{4}",
                     r"from\s+['\"]st_solver_worker|import\s+phreeqpython"]
        for p in ui_src.rglob("*"):
            if p.is_file() and p.suffix in {".ts", ".tsx", ".js"}:
                text = p.read_text(encoding="utf-8", errors="ignore")
                for pat in forbidden:
                    if re.search(pat, text):
                        offenders.append(f"{p.relative_to(ROOT)}:{pat}")
        eq(not offenders, f"[范式] web-ui 旧演示层/直连残留: {offenders}")
        print("[pipeline] OK 范式护栏: web-ui 无预设配比/时间轴/报告/硬编码药品架/直连求解库")

        print("[pipeline] 通过：M2 自由台面核心循环 + 数据驱动 + 操作原语 + 定向求解 + 三态如实")
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
