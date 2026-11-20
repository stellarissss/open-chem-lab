"""常驻 worker 入口：定期心跳，等待后续切片接入求解循环。

设计约束（见 01-Architecture.md）：
- 求解在独立 worker，不占 16.7ms 帧预算。
- 本骨架不做任何真实求解、不引入任何化学数据。
"""
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
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    LOG.info("solver-worker 0.1.0 已启动（骨架，未接求解逻辑）")
    tick = 0
    while _running:
        tick += 1
        LOG.info("heartbeat #%d", tick)
        # 等待可被信号中断，保证 SIGTERM 快速退出（Compose 优雅停机）。
        for _ in range(int(TICK_SECONDS * 10)):
            if not _running:
                break
            time.sleep(0.1)
    LOG.info("solver-worker 已退出")
    return 0


if __name__ == "__main__":
    sys.exit(main())
