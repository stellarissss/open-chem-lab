# reaktoro-service 占位镜像：不接真实求解、不预装 reaktoro，仅保留独立服务形态与契约声明。
# 正式镜像为 conda 基础镜像 + reaktoro + gRPC server，并在此固定版本与 LGPL-2.1 §6 可替换性声明。
FROM alpine:3.20
LABEL org.opencontainers.image.title="st-reaktoro-service" \
      org.opencontainers.image.description="placeholder - LGPL-2.1 dynamically-linkable service" \
      org.opencontainers.image.licenses="LGPL-2.1-or-later"

# 占位进程：仅声明自身就绪，不监听求解端口。
CMD ["sh", "-c", "echo 'reaktoro-service placeholder: no solver attached' && sleep infinity"]
