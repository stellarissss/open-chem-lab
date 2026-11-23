# solver-worker（仓库根为 build context）
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# 安装 uv 并按 lockfile 同步求解依赖（phreeqpython / chempy），版本锁定、可复现。
# 从已配置的镜像源安装 uv（镜像站可达性优于默认 PyPI / ghcr），避免构建卡在外网拉取。
RUN pip install --no-cache-dir uv==0.10.0 --index-url https://mirrors.aliyun.com/pypi/simple/
COPY packages/solver-worker/pyproject.toml packages/solver-worker/uv.lock ./
RUN uv sync --frozen --no-install-project

COPY packages/solver-worker/src ./src
# solver 求解时读取已物化 ruleset 与权威源 .dat 快照（只读事实层）。
COPY content/materialized ./content/materialized
COPY content/ai-crosscheck ./content/ai-crosscheck

ENV PYTHONPATH=/app/src
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV HEARTBEAT_SECONDS=5
USER nobody
# 默认开启本地 HTTP 端点：gateway 经 SOLVER_URL 调用 solve / solve/timeline。
CMD ["python", "-m", "st_solver_worker", "--http"]
