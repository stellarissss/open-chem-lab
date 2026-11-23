import Fastify from "fastify";
import websocket from "@fastify/websocket";
import {
  PHENOMENON_SCHEMA_VERSION,
  SOLUTION_SPECIATION_SCHEMA_VERSION,
  TIMELINE_SCHEMA_VERSION,
} from "@st/protocol";
import type { SolutionSpeciation, SpeciationTimeline, PhenomenonDirective } from "@st/protocol";

const PORT = Number(process.env.PORT ?? 3001);
const HOST = process.env.HOST ?? "0.0.0.0";
const SERVICE_VERSION = process.env.SERVICE_VERSION ?? "0.1.0";
// 求解 worker 的本地 HTTP 端点；容器编排里指向 solver-worker:8765。
// web-ui 只访问 gateway，绝不直连求解库（01 第六节依赖规则）。
const SOLVER_URL = process.env.SOLVER_URL ?? "http://127.0.0.1:8765";
const startedAt = Date.now();

const app = Fastify({ logger: true });

await app.register(websocket);

/** 本地求解端点代理：gateway 是唯一对外入口，求解细节不暴露给表现层。 */
async function callSolver<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${SOLVER_URL}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(10_000),
  });
  if (!res.ok) throw new Error(`solver ${path} responded ${res.status}`);
  return (await res.json()) as T;
}

/**
 * 时间轴缓存：键 = 体系名。扫描定义在 solver 侧固定（01 第五节「内容寻址键」），
 * 同一体系的 timeline_id 由 sha256(canonical(scan_def)+ruleset_version) 派生。
 * 命中即完全跳过 solver 调用——响应头 x-cache=hit / x-solve-calls=0 供复用实证。
 */
const timelineCache = new Map<string, { timeline: SpeciationTimeline; solve_calls: number }>();

// 健康检查：前端壳页与 Compose healthcheck 共用。返回体保持最小、稳定。
app.get("/api/v1/health", async () => ({
  status: "ok" as const,
  service: "gateway",
  version: SERVICE_VERSION,
  protocol: PHENOMENON_SCHEMA_VERSION,
  uptime_ms: Date.now() - startedAt,
}));

// 物种读取接口：返回体即 st.solution_speciation.v1，不包裹、不加工数值。
app.post("/api/v1/speciation", async (request, reply) => {
  try {
    const body = request.body as Record<string, unknown> | null;
    if (!body || !Array.isArray(body.substances)) {
      return reply.code(400).send({ error: "expected { container_id?, substances: [...] }" });
    }
    const spec = await callSolver<SolutionSpeciation>("/solve", body);
    reply.header("x-protocol", SOLUTION_SPECIATION_SCHEMA_VERSION);
    return reply.send(spec);
  } catch (err) {
    request.log.error(err);
    return reply.code(502).send({ error: "solver unavailable" });
  }
});

// 现象成因溯源：返回 st.phenomenon.v1 指令列表（只供面板展示 trigger，不渲染）。
app.post("/api/v1/speciation/phenomena", async (request, reply) => {
  try {
    const directives = await callSolver<PhenomenonDirective[]>(
      "/solve/phenomena",
      request.body ?? {},
    );
    reply.header("x-protocol", PHENOMENON_SCHEMA_VERSION);
    return reply.send(directives);
  } catch (err) {
    request.log.error(err);
    return reply.code(502).send({ error: "solver unavailable" });
  }
});

// 时间轴读取接口：返回体即 st.timeline.v1。
app.get("/api/v1/timeline", async (request, reply) => {
  const system = ((request.query as { system?: string }).system ?? "strong");
  reply.header("x-protocol", TIMELINE_SCHEMA_VERSION);

  const cached = timelineCache.get(system);
  if (cached) {
    reply.header("x-cache", "hit");
    reply.header("x-solve-calls", "0");
    return reply.send(cached.timeline);
  }

  try {
    const envelope = await callSolver<{
      timeline: SpeciationTimeline;
      solve_calls: number;
    }>("/solve/timeline", { system });
    timelineCache.set(system, envelope);
    reply.header("x-cache", "miss");
    reply.header("x-solve-calls", String(envelope.solve_calls));
    return reply.send(envelope.timeline);
  } catch (err) {
    request.log.error(err);
    return reply.code(502).send({ error: "solver unavailable" });
  }
});

// WS 握手：保留 echo（兼容），并预留 phenomenon 订阅通道供 spec-005 下发现象指令。
// 本切片只建立订阅关系与确认，不承载渲染逻辑。
const phenomenonSubscribers = new Set<{ send: (data: string) => void }>();

app.register(async (instance) => {
  instance.get("/ws", { websocket: true }, (socket) => {
    socket.send(
      JSON.stringify({ type: "welcome", protocol: PHENOMENON_SCHEMA_VERSION }),
    );
    socket.on("message", (raw: Buffer) => {
      let msg: { type?: string; channel?: string };
      try {
        msg = JSON.parse(raw.toString()) as { type?: string; channel?: string };
      } catch {
        socket.send(JSON.stringify({ type: "echo", payload: raw.toString() }));
        return;
      }
      if (msg.type === "subscribe" && msg.channel === "phenomenon") {
        phenomenonSubscribers.add(socket);
        socket.send(JSON.stringify({
          type: "subscribed",
          channel: "phenomenon",
          protocol: PHENOMENON_SCHEMA_VERSION,
        }));
        return;
      }
      if (msg.type === "unsubscribe" && msg.channel === "phenomenon") {
        phenomenonSubscribers.delete(socket);
        socket.send(JSON.stringify({ type: "unsubscribed", channel: "phenomenon" }));
        return;
      }
      socket.send(JSON.stringify({ type: "echo", payload: raw.toString() }));
    });
    socket.on("close", () => phenomenonSubscribers.delete(socket));
  });
});

try {
  await app.listen({ port: PORT, host: HOST });
} catch (err) {
  app.log.error(err);
  process.exit(1);
}
