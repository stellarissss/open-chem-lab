# solver-worker 骨架（仓库根为 build context）
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY packages/solver-worker/pyproject.toml packages/solver-worker/uv.lock ./
COPY packages/solver-worker/src ./src
# 骨架阶段零第三方依赖，直接以 src 运行；spec-003 接入求解器后改为 uv sync --frozen。
ENV PYTHONPATH=/app/src
ENV HEARTBEAT_SECONDS=5
USER nobody
CMD ["python", "-m", "st_solver_worker"]
