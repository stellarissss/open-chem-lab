"""部署可达性 e2e：验证 gateway→solver 跨地址链路（P0 回归护栏）。

失效模式：solver 只绑 127.0.0.1 时，容器编排里 gateway 经
http://solver-worker:8765 跨容器调用必然 connection refused。
本测试从本机非回环 IP 访问 solver，精确覆盖该模式——绑定回环则连接失败。

纯标准库，不需要 docker build；CI 与本地均可跑。
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENV_PY = ROOT / "packages/solver-worker/.venv/bin/python"
PORT = 18765  # 固定高端口，避免与默认 8765 冲突


def local_nonloop_ip() -> str:
    """取本机非回环 IPv4（容器场景的 '外部' 地址）。"""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))  # 只是选路，不发报文
        return s.getsockname()[0]


def wait_health(url: str, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False


def main() -> int:
    ip = local_nonloop_ip()
    python = sys.executable if VENV_PY.exists() else sys.executable
    env = dict(os.environ, PYTHONPATH=str(ROOT / "packages/solver-worker/src"), HOST="0.0.0.0")
    proc = subprocess.Popen(
        [python, "-m", "st_solver_worker", "--http", "--port", str(PORT)],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        base = f"http://{ip}:{PORT}"
        if not wait_health(base + "/health"):
            print(f"[e2e] FAIL 跨地址 /health 不可达 ({base})——solver 是否仍绑回环？")
            return 1
        print(f"[e2e] OK 跨地址 /health 可达 ({base})")

        body = json.dumps({
            "container_id": "e2e",
            "substances": [{"compound_id": "hcl", "concentration_mol_L": 0.1, "volume_L": 1.0}],
        }).encode()
        req = urllib.request.Request(base + "/solve", data=body,
                                     headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            result = json.loads(r.read())
        if result.get("outcome") != "solved" or not (1.0 < result.get("ph", 0) < 1.2):
            print(f"[e2e] FAIL 跨地址 /solve 结果异常: outcome={result.get('outcome')} ph={result.get('ph')}")
            return 1
        print(f"[e2e] OK 跨地址 /solve: outcome={result['outcome']} ph={result['ph']:.4f}")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
