"""solver-worker HTTP 端点（spec-003 起，内部函数 + 轻量本地 HTTP）。

用标准库 http.server，零新增依赖；由 gateway 经 SOLVER_URL 调用，web-ui 不直连。
绑定地址由 --host / HOST 决定：本地默认 127.0.0.1，容器编排设 0.0.0.0 供跨容器可达。

端点：
    GET  /health                 → {"status":"ok","service":"solver-worker"}
    POST /solve                  → st.solution_speciation.v1
    POST /solve/phenomena        → [st.phenomenon.v1]
    POST /solve/heat             → 错误操作后果（浓酸入水放热）
    POST /solve/timeline         → st.timeline.v1（滴定关键帧 + pH 曲线）
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from . import phenomena, solver, timeline

# 服务版本与全仓 package.json 对齐（0.1.0）；可由环境覆盖，供缓存键与排障核对。
SERVICE_VERSION = os.environ.get("SERVICE_VERSION", "0.1.0")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        pass  # 静默，避免心跳式日志

    def _send(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, {"status": "ok", "service": "solver-worker", "version": SERVICE_VERSION})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self._read_json()
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid json"})
            return
        try:
            if self.path == "/solve":
                result = solver.solve(payload)
                self._send(200, result)
            elif self.path == "/solve/phenomena":
                spec = solver.solve(payload)
                directives = phenomena.derive(spec, payload.get("timestamp_ms", 0))
                self._send(200, directives)
            elif self.path == "/solve/heat":
                heat = solver.solve_heat(
                    payload.get("compound_ids", []),
                    substances=payload.get("substances"),
                    addition_order=payload.get("addition_order", "acid_into_water"),
                )
                # 错误操作后果的现象指令随热结果一并返回（spec-005 飞溅链路）：
                # splash 由加入顺序派生、temperature_change 由温升派生。
                heat["directives"] = phenomena.heat_directives(
                    heat, container_id=payload.get("container_id", "heat-beaker"),
                    timestamp_ms=payload.get("timestamp_ms", 0))
                self._send(200, heat)
            elif self.path == "/solve/timeline":
                ratios = payload.get("ratios")
                spec, solve_calls = timeline.build_timeline(
                    system=payload.get("system", "strong"),
                    ratios=tuple(ratios) if ratios else None,
                    container_id=payload.get("container_id", "titration-beaker"),
                )
                # 求解调用计数随响应返回，供缓存复用实证（关键帧数 == solve_calls）。
                # solver_version 供 gateway 内容寻址缓存键纳入 solver_ver 维度。
                self._send(200, {"timeline": spec, "solve_calls": solve_calls,
                                 "solver_version": SERVICE_VERSION})
            else:
                self._send(404, {"error": "not found"})
        except Exception as exc:  # 诚实降级，不把内部异常当科学结论
            self._send(500, {"outcome": "degraded", "reason": str(exc)})


def serve(host: str | None = None, port: int = 8765) -> None:
    host = host or os.environ.get("HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"[solver-worker] HTTP listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
