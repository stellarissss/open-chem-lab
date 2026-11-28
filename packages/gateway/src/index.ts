import Fastify from "fastify";
import websocket from "@fastify/websocket";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import {
  PHENOMENON_SCHEMA_VERSION,
  REPORT_SCHEMA_VERSION,
  SOLUTION_SPECIATION_SCHEMA_VERSION,
  TIMELINE_SCHEMA_VERSION,
  BENCH_WORLD_SCHEMA_VERSION,
  OPERATION_EVENT_SCHEMA_VERSION,
  CONTAINER_STATE_SCHEMA_VERSION,
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

/**
 * 台面目录（008）：试剂架 / 器材架从物化 ruleset 派生，web-ui 不再硬编码药品表。
 * 路径由 ST_REPO_ROOT 指定（容器内为 /app），本地默认上溯仓库根。规则集只读、
 * 构建期物化，gateway 启动时加载一次；版本随 ruleset_version 暴露供前端对齐。
 */

const REPO_ROOT = process.env.ST_REPO_ROOT
  ?? path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
let benchCatalogCache: { ruleset_version: string; reagents: unknown[]; apparatus: unknown[] } | null = null;

function loadBenchCatalog(): { ruleset_version: string; reagents: unknown[]; apparatus: unknown[] } {
  if (benchCatalogCache) return benchCatalogCache;
  const ruleset = JSON.parse(readFileSync(path.join(REPO_ROOT, "content/materialized/ruleset.json"), "utf8")) as {
    ruleset_version?: string;
    compounds?: Array<Record<string, unknown>>;
    apparatus?: unknown[];
  };
  const reagents = (ruleset.compounds ?? [])
    .filter((c) => c.reagent_solution && typeof c.reagent_solution === "object")
    .map((c) => {
      const rs = c.reagent_solution as Record<string, unknown>;
      return {
        compound_id: c.compound_id,
        label: (c.names as { zh?: string } | undefined)?.zh ?? String(c.compound_id),
        formula: c.formula,
        concentration_mol_L: rs.concentration_mol_L,
        hazard: rs.hazard ?? false,
        solvent: rs.solvent ?? false,
        applicability: rs.applicability ?? null,
        solution_color: (c.presentation as { solution_color?: string } | undefined)?.solution_color ?? null,
      };
    });
  benchCatalogCache = {
    ruleset_version: String(ruleset.ruleset_version ?? "unknown"),
    reagents,
    apparatus: ruleset.apparatus ?? [],
  };
  return benchCatalogCache;
}

app.get("/api/v1/bench/catalog", async (_request, reply) => {
  reply.header("x-protocol", BENCH_WORLD_SCHEMA_VERSION);
  return reply.send(loadBenchCatalog());
});

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
 * 失效由 solver_ver / ruleset_ver 双版本驱动（01 §5.2）：命中时比对 solver_version，
 * 版本漂移即逐出重算；ruleset 变更体现为 timeline_id 变化，由 web 侧按 id 识别。
 */
const timelineCache = new Map<string, { timeline: SpeciationTimeline; solve_calls: number; solverVersion: string }>();
let lastSolverVersion = "unknown";

// 健康检查：前端壳页与 Compose healthcheck 共用。返回体保持最小、稳定。
app.get("/api/v1/health", async () => ({
  status: "ok" as const,
  service: "gateway",
  version: SERVICE_VERSION,
  solver_version: lastSolverVersion,
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

// 错误操作后果（浓硫酸稀释）：代理 solver 热结果 + 派生现象指令（spec-005 飞溅链路）。
// 返回体含 heat 字段（ΔT / splash_risk）与 directives（splash / temperature_change）。
// web-ui 只认指令 ID 与物理量，求解细节不外泄。
function broadcastPhenomena(directives: PhenomenonDirective[]): void {
  const payload = JSON.stringify({ type: "phenomenon", directives });
  for (const sub of phenomenonSubscribers) {
    try { sub.send(payload); } catch { /* 断连订阅者由 close 事件清理 */ }
  }
}

app.post("/api/v1/heat", async (request, reply) => {
  try {
    const body = request.body as Record<string, unknown> | null;
    if (!body || !Array.isArray(body.substances)) {
      return reply.code(400).send({ error: "expected { container_id?, addition_order?, substances: [...] }" });
    }
    const heat = await callSolver<Record<string, unknown> & { directives: PhenomenonDirective[] }>(
      "/solve/heat", body);
    reply.header("x-protocol", PHENOMENON_SCHEMA_VERSION);
    if (heat.directives?.length) broadcastPhenomena(heat.directives);
    return reply.send(heat);
  } catch (err) {
    request.log.error(err);
    return reply.code(502).send({ error: "solver unavailable" });
  }
});

// 操作原语事件上报（008）：st.operation_event.v1 经 gateway 校验形状后计入会话计数。
// 台面是持续沙盘、不存「实验」；事件用于可观测性（计数回显）与范式证据，不入库留存。
let operationEventCount = 0;
app.post("/api/v1/bench/operation", async (request, reply) => {
  const body = request.body as Record<string, unknown> | null;
  if (!body || typeof body.event_id !== "string" || typeof body.op_type !== "string"
      || typeof body.timestamp_ms !== "number") {
    return reply.code(400).send({ error: "expected st.operation_event.v1 core fields" });
  }
  operationEventCount += 1;
  reply.header("x-protocol", OPERATION_EVENT_SCHEMA_VERSION);
  return reply.send({ accepted: true, count: operationEventCount });
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
  if (cached && cached.solverVersion === lastSolverVersion) {
    reply.header("x-cache", "hit");
    reply.header("x-solve-calls", "0");
    return reply.send(cached.timeline);
  }

  try {
    const envelope = await callSolver<{
      timeline: SpeciationTimeline;
      solve_calls: number;
      solver_version?: string;
    }>("/solve/timeline", { system });
    const solverVersion = envelope.solver_version ?? "unknown";
    lastSolverVersion = solverVersion;
    timelineCache.set(system, {
      timeline: envelope.timeline,
      solve_calls: envelope.solve_calls,
      solverVersion,
    });
    reply.header("x-cache", "miss");
    reply.header("x-solve-calls", String(envelope.solve_calls));
    return reply.send(envelope.timeline);
  } catch (err) {
    request.log.error(err);
    return reply.code(502).send({ error: "solver unavailable" });
  }
});

// 实验报告读取接口（spec-006）：gateway 只做代理，汇编在 solver-worker 侧只读复用
// solve/timeline/ruleset 出口，不在网关层重算任何化学量。web-ui 不直连求解库。
app.post("/api/v1/report", async (request, reply) => {
  try {
    const body = request.body as Record<string, unknown> | null;
    if (!body) {
      return reply.code(400).send({ error: "expected report request body" });
    }
    const built = await callSolver<Record<string, unknown>>("/solve/report", {
      operations: body.operations ?? [],
      substances: body.substances ?? [],
      system: body.system ?? "strong",
      container_id: body.container_id ?? "report-beaker",
    });
    reply.header("x-protocol", REPORT_SCHEMA_VERSION);
    return reply.send(built);
  } catch (err) {
    request.log.error(err);
    return reply.code(502).send({ error: "solver unavailable" });
  }
});

// WS 握手：echo（兼容）+ phenomenon 频道（兼容旧）+ container_state 按 container_id 定向订阅（008）。
// container_state 替换旧 phenomenon 全局广播：订阅者的 key 为 container_id，只收本容器的状态。
type WsSocket = { send: (data: string) => void };
const phenomenonSubscribers = new Set<WsSocket>();
/** container_id → 订阅该容器的 socket 集合。定向推送，多容器现象不串扰。 */
const containerSubscribers = new Map<string, Set<WsSocket>>();

/** 定向推送 container_state：只发给订阅该 container_id 的客户端。 */
function pushContainerState(containerId: string, payload: unknown): number {
  const subs = containerSubscribers.get(containerId);
  if (!subs || subs.size === 0) return 0;
  const data = JSON.stringify(payload);
  let sent = 0;
  for (const sub of subs) {
    try { sub.send(data); sent += 1; } catch { /* 断连由 close 清理 */ }
  }
  return sent;
}

/** 倾倒结算：求解容器组成 → 定向推送 container_state → 同步返回（前端无需等 WS）。 */
app.post("/api/v1/bench/container-state", async (request, reply) => {
  const started = Date.now();
  try {
    const body = request.body as Record<string, unknown> | null;
    if (!body || typeof body.container_id !== "string" || !Array.isArray(body.substances)) {
      return reply.code(400).send({ error: "expected { container_id, substances: [...] }" });
    }
    const containerId = body.container_id;
    const payload = {
      container_id: containerId,
      substances: body.substances,
      addition_order: body.addition_order ?? "acid_into_water",
    };
    const [spec, directives] = await Promise.all([
      callSolver<Record<string, unknown>>("/solve", payload),
      callSolver<unknown[]>("/solve/phenomena", payload),
    ]);
    const state = {
      schema_version: CONTAINER_STATE_SCHEMA_VERSION,
      container_id: containerId,
      speciation: spec,
      directives,
      solve_latency_ms: Date.now() - started,
      solver_version: String(spec.solver_version ?? "unknown"),
      ruleset_version: String(spec.ruleset_version ?? ""),
    };
    const delivered = pushContainerState(containerId, {
      type: "container_state",
      ...state,
    });
    reply.header("x-protocol", CONTAINER_STATE_SCHEMA_VERSION);
    reply.header("x-container-delivered", String(delivered));
    return reply.send(state);
  } catch (err) {
    request.log.error(err);
    return reply.code(502).send({ error: "solver unavailable" });
  }
});

app.register(async (instance) => {
  instance.get("/ws", { websocket: true }, (socket) => {
    socket.send(
      JSON.stringify({ type: "welcome", protocol: PHENOMENON_SCHEMA_VERSION }),
    );
    socket.on("message", (raw: Buffer) => {
      let msg: { type?: string; channel?: string; container_id?: string };
      try {
        msg = JSON.parse(raw.toString()) as { type?: string; channel?: string; container_id?: string };
      } catch {
        socket.send(JSON.stringify({ type: "echo", payload: raw.toString() }));
        return;
      }
      if (msg.type === "subscribe" && msg.channel === "phenomenon") {
        phenomenonSubscribers.add(socket);
        socket.send(JSON.stringify({
          type: "subscribed", channel: "phenomenon", protocol: PHENOMENON_SCHEMA_VERSION,
        }));
        return;
      }
      if (msg.type === "unsubscribe" && msg.channel === "phenomenon") {
        phenomenonSubscribers.delete(socket);
        socket.send(JSON.stringify({ type: "unsubscribed", channel: "phenomenon" }));
        return;
      }
      // 008：按 container_id 定向订阅容器状态（替换全局广播）
      if (msg.type === "subscribe" && msg.channel === "container_state" && msg.container_id) {
        let set = containerSubscribers.get(msg.container_id);
        if (!set) { set = new Set(); containerSubscribers.set(msg.container_id, set); }
        set.add(socket);
        socket.send(JSON.stringify({
          type: "subscribed", channel: "container_state", container_id: msg.container_id,
          protocol: CONTAINER_STATE_SCHEMA_VERSION,
        }));
        return;
      }
      if (msg.type === "unsubscribe" && msg.channel === "container_state" && msg.container_id) {
        containerSubscribers.get(msg.container_id)?.delete(socket);
        socket.send(JSON.stringify({ type: "unsubscribed", channel: "container_state", container_id: msg.container_id }));
        return;
      }
      socket.send(JSON.stringify({ type: "echo", payload: raw.toString() }));
    });
    socket.on("close", () => {
      phenomenonSubscribers.delete(socket);
      for (const set of containerSubscribers.values()) set.delete(socket);
    });
  });
});

try {
  await app.listen({ port: PORT, host: HOST });
} catch (err) {
  app.log.error(err);
  process.exit(1);
}
