"""常驻 worker 入口：默认心跳；--http 启动本地求解 HTTP 端点。

设计约束（见 01-Architecture.md）：
- 求解在独立 worker，不占 16.7ms 帧预算。
- spec-004 起 gateway 经 SOLVER_URL 调本 HTTP 端点；绑定地址由 HOST 控制，
  本地默认回环、容器编排设 0.0.0.0，web-ui 始终只经 gateway（保持解耦）。
"""
import argparse
import logging
import os
import signal
import sys
import time

LOG = logging.getLogger("st-solver-worker")
TICK_SECONDS = float(os.environ.get("HEARTBEAT_SECONDS", "5"))
_running = True


def _stop(_signum: int, _frame: object) -> None:
    global _running
    _running = False


def main() -> int:
    parser = argparse.ArgumentParser(description="ST solver-worker")
    parser.add_argument("--http", action="store_true", help="启动本地 HTTP 求解端点")
    parser.add_argument("--port", type=int, default=8765, help="HTTP 端口（默认 8765）")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"),
                        help="绑定地址；单机本地默认回环，容器编排经 HOST=0.0.0.0 覆盖")
    args, _ = parser.parse_known_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.http:
        from .server import serve
        serve(host=args.host, port=args.port)
        return 0

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    LOG.info("solver-worker %s 已启动（HTTP 求解端点用 --http 开启）",
             os.environ.get("SERVICE_VERSION", "0.1.0"))
    tick = 0
    while _running:
        tick += 1
        LOG.info("heartbeat #%d", tick)
        for _ in range(int(TICK_SECONDS * 10)):
            if not _running:
                break
            time.sleep(0.1)
    LOG.info("solver-worker 已退出")
    return 0


if __name__ == "__main__":
    sys.exit(main())
