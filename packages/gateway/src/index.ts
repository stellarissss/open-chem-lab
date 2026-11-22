import Fastify from "fastify";
import websocket from "@fastify/websocket";
import { PHENOMENON_SCHEMA_VERSION } from "@st/protocol";

const PORT = Number(process.env.PORT ?? 3001);
const HOST = process.env.HOST ?? "0.0.0.0";
const SERVICE_VERSION = process.env.SERVICE_VERSION ?? "0.1.0";
const startedAt = Date.now();

const app = Fastify({ logger: true });

await app.register(websocket);

// 健康检查：前端壳页与 Compose healthcheck 共用。返回体保持最小、稳定。
app.get("/api/v1/health", async () => ({
  status: "ok" as const,
  service: "gateway",
  version: SERVICE_VERSION,
  protocol: PHENOMENON_SCHEMA_VERSION,
  uptime_ms: Date.now() - startedAt,
}));

// WS 握手：仅建立连接 + echo，不承载求解逻辑。
// 鉴权、会话与 st.phenomenon.v1 指令下发按切片接入。
app.register(async (instance) => {
  instance.get("/ws", { websocket: true }, (socket) => {
    socket.send(
      JSON.stringify({ type: "welcome", protocol: PHENOMENON_SCHEMA_VERSION }),
    );
    socket.on("message", (raw: Buffer) => {
      socket.send(JSON.stringify({ type: "echo", payload: raw.toString() }));
    });
  });
});

try {
  await app.listen({ port: PORT, host: HOST });
} catch (err) {
  app.log.error(err);
  process.exit(1);
}
