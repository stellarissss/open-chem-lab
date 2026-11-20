# reaktoro-service 占位镜像（spec-001）
# 本切片不接真实求解、不预装 reaktoro，仅保留独立服务形态与契约声明。
# 正式镜像在求解切片接入时改为 conda 基础镜像 + reaktoro + gRPC server，
# 并在此固定版本与 LGPL-2.1 §6 可替换性声明。
FROM alpine:3.20
LABEL org.opencontainers.image.title="st-reaktoro-service" \
      org.opencontainers.image.description="placeholder — LGPL-2.1 dynamically-linkable service (spec-001)" \
      org.opencontainers.image.licenses="LGPL-2.1-or-later"

# 占位进程：仅声明自身就绪，不监听求解端口。
CMD ["sh", "-c", "echo 'reaktoro-service placeholder (spec-001): no solver attached' && sleep infinity"]
