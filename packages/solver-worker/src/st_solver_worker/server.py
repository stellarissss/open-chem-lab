"""solver-worker 本地 HTTP 端点（spec-003，内部函数 + 轻量本地 HTTP）。

用标准库 http.server，零新增依赖、不接 gateway 路由（本切片保持独立 worker 解耦）。
供测试与内部调用；绑定 127.0.0.1，仅回环可达。

端点：
    GET  /health                 → {"status":"ok","service":"solver-worker"}
    POST /solve                  → st.solution_speciation.v1
    POST /solve/phenomena        → [st.phenomenon.v1]
    POST /solve/heat             → 错误操作后果（浓酸入水放热）
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from . import phenomena, solver


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
            self._send(200, {"status": "ok", "service": "solver-worker", "version": "0.2.0"})
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
                self._send(200, solver.solve_heat(
                    payload.get("compound_ids", []),
                    substances=payload.get("substances"),
                ))
            else:
                self._send(404, {"error": "not found"})
        except Exception as exc:  # 诚实降级，不把内部异常当科学结论
            self._send(500, {"outcome": "degraded", "reason": str(exc)})


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"[solver-worker] HTTP listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
