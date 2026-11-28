import { create } from "zustand";
import type { PhenomenonDirective, SolutionSpeciation } from "@st/protocol";
import {
  fillRatio, integratePour, liquidCounterRotation, tiltFromPointer,
  type PourState, type VesselGeometry,
} from "./benchPhysics";
// 写实 SVG 经 ?url 导入：Vite 在 dev 与 Docker build 都把资产拷入产物（旧范式已验证可行）。
import beakerSvg from "../../../assets/apparatus/beaker_250ml.svg?url";
import cylinderSvg from "../../../assets/apparatus/graduated-cylinder.svg?url";
import dropperSvg from "../../../assets/apparatus/dropper.svg?url";
import roundFlaskSvg from "../../../assets/apparatus/round-flask.svg?url";

// 唯一取数口：/api/* 与 /ws 全部经 gateway；web-ui 不直连求解库（01 第六节依赖规则）。

export interface SpeciesRow {
  name: string;
  concentration: number;
  activity?: number;
  moleFraction?: number;
  phase?: string;
}

/** 物种面板统一视图模型（数值原样呈现不加工）。 */
export interface PanelData {
  containerId: string;
  ph: number;
  ionicStrength: number;
  temperatureK?: number;
  outcome: string;
  confidence?: number;
  reason?: string;
  species: SpeciesRow[];
  hiddenReactions: string[];
  phenomena: PhenomenonDirective[];
  timestampMs?: number;
  speciationId?: string;
  rulesetVersion?: string;
}

export function fromSpeciation(spec: SolutionSpeciation): PanelData {
  return {
    containerId: spec.container_id,
    ph: spec.ph,
    ionicStrength: spec.ionic_strength,
    temperatureK: spec.temperature_K,
    outcome: spec.outcome ?? "solved",
    confidence: spec.confidence,
    reason: spec.reason,
    species: spec.species.map((s) => ({
      name: s.species_id,
      concentration: s.concentration_mol_L,
      activity: s.activity,
      moleFraction: s.mole_fraction,
    })),
    hiddenReactions: spec.hidden_reactions ?? [],
    phenomena: [],
    timestampMs: spec.timestamp_ms,
    speciationId: spec.speciation_id,
    rulesetVersion: spec.ruleset_version,
  };
}

/** 试剂架条目：gateway /bench/catalog 从物化 ruleset 派生，前端零硬编码。 */
export interface ReagentOption {
  compound_id: string;
  label: string;
  formula: string;
  concentration_mol_L: number;
  hazard: boolean;
  solvent: boolean;
  applicability: string | null;
  solution_color: string | null;
}

/** 器材架条目：apparatus 卡派生。 */
export interface ApparatusOption {
  apparatus_id: string;
  names: { zh: string; en: string };
  type: string;
  capacity_mL?: number;
  asset?: string;
  graduations?: number[];
}

/** 容器几何（mm），来自 apparatus 卡容量与写实比例，用于倾角物理。 */
const GEOMETRY: Record<string, VesselGeometry> = {
  beaker_250ml: { mouthWidth_mm: 78, height_mm: 95, capacity_mL: 250 },
  graduated_cylinder_100ml: { mouthWidth_mm: 26, height_mm: 160, capacity_mL: 100 },
  reagent_bottle: { mouthWidth_mm: 22, height_mm: 110, capacity_mL: 250 },
  dropper: { mouthWidth_mm: 4, height_mm: 90, capacity_mL: 2 },
};
const DEFAULT_GEOMETRY: VesselGeometry = { mouthWidth_mm: 40, height_mm: 90, capacity_mL: 100 };

/** 台面上一件器材实例（试剂瓶与容器统一，皆为可摆放容器）。 */
export interface BenchItem {
  instance_id: string;
  apparatus_id: string;
  kind: "vessel" | "reagent_bottle";
  label: string;
  x: number; // px 左上角
  y: number;
  w: number;
  h: number;
  rotation: number; // 度，容器倾角
  volume_mL: number; // 操作产生
  contents: Array<{ compound_id: string; concentration_mol_L: number; volume_L: number }>;
  reagent?: ReagentOption;
  asset?: string;
}

export type BenchMode = "idle" | "dragging" | "pouring";
export interface NearbyAction {
  sourceId: string;
  targetId: string;
  x: number;
  y: number;
}

interface DragOffset { dx: number; dy: number }

export interface LabState {
  // 目录（数据驱动）
  reagents: ReagentOption[];
  apparatus: ApparatusOption[];
  rulesetVersion: string;
  catalogLoaded: boolean;
  loadCatalog: () => Promise<void>;

  // 台面
  items: BenchItem[];
  benchW: number;
  benchH: number;
  selectedId: string | null;
  mode: BenchMode;
  nearby: NearbyAction | null;
  pourSourceId: string | null;
  pourTargetId: string | null;
  dragId: string | null;
  dragOffset: DragOffset | null;

  // 求解
  panelByContainer: Record<string, PanelData>;
  selectedPanel: PanelData | null;
  loading: boolean;
  error: string | null;
  opCount: number;

  // 操作
  placeFromRack: (kind: "reagent" | "apparatus", id: string) => void;
  startDrag: (instanceId: string, px: number, py: number) => void;
  moveDrag: (px: number, py: number) => void;
  endDrag: () => void;
  select: (instanceId: string) => void;
  beginPour: (sourceId: string, targetId: string) => void;
  updatePourTilt: (pointerX: number, pointerY: number) => void;
  endPour: () => Promise<void>;
  closeItem: (instanceId: string) => void;
  clearBench: () => void;
  reportOp: (opType: string, detail: Record<string, unknown>) => Promise<void>;

  // WS
  wsStatus: "off" | "connecting" | "on" | "error";
  connectWs: () => () => void;
}

const ASSET_URLS: Record<string, string> = {
  beaker_250ml: beakerSvg,
  graduated_cylinder_100ml: cylinderSvg,
  dropper: dropperSvg,
  reagent_bottle: roundFlaskSvg,
};

let instanceSeq = 0;
const nextId = (prefix: string) => `${prefix}-${++instanceSeq}`;

/** 轴对齐矩形重叠（含 2px 间隙），保证器材不可重叠。 */
export function rectsOverlap(
  ax: number, ay: number, aw: number, ah: number, bx: number, by: number, bw: number, bh: number,
): boolean {
  const gap = 2;
  return ax < bx + bw + gap && ax + aw + gap > bx && ay < by + bh + gap && ay + ah + gap > by;
}

function centerDist(a: BenchItem, b: BenchItem): number {
  return Math.hypot((a.x + a.w / 2) - (b.x + b.w / 2), (a.y + a.h / 2) - (b.y + b.h / 2));
}

export function geometryOf(item: BenchItem): VesselGeometry {
  return GEOMETRY[item.apparatus_id] ?? DEFAULT_GEOMETRY;
}

/** 液面表现色（presentation 层；精确变色由求解后的现象指令派生）。 */
export function liquidColorOf(item: BenchItem): string | null {
  const explicit = item.reagent?.solution_color;
  if (explicit && explicit !== "无色") return explicit;
  const ids = item.contents.map((c) => c.compound_id);
  if (ids.includes("phenolphthalein")) return "#f2b8c6";
  if (ids.includes("sulfuric_acid_conc")) return "#d9c27a";
  if (ids.includes("naoh") || ids.includes("koh")) return "#cfe3d8";
  if (ids.includes("hcl")) return "#e8dfc9";
  return null;
}

/** 就近检测：两容器足够近 → 返回倾倒操作锚点（临近交互范式）。
 *  源 = 有内容可倒出的一方（优先试剂瓶），目标 = 另一方——从有液体处倒向空/接收处。 */
export function detectNearby(a: BenchItem, b: BenchItem, threshold = 130): NearbyAction | null {
  if (a.instance_id === b.instance_id) return null;
  if (a.kind !== "vessel" && b.kind !== "vessel") return null;
  if (centerDist(a, b) > threshold) return null;
  const aHas = a.volume_mL > 0 && a.contents.length > 0;
  const bHas = b.volume_mL > 0 && b.contents.length > 0;
  let source: BenchItem, target: BenchItem;
  if (aHas && !bHas) { source = a; target = b; }
  else if (!aHas && bHas) { source = b; target = a; }
  else if (a.kind === "reagent_bottle") { source = a; target = b; }
  else if (b.kind === "reagent_bottle") { source = b; target = a; }
  else { source = a; target = b; }
  return {
    sourceId: source.instance_id, targetId: target.instance_id,
    x: (a.x + a.w / 2 + b.x + b.w / 2) / 2,
    y: Math.min(a.y, b.y) + 8,
  };
}

/** WS 单例（StrictMode 双挂载防护）。 */
let stateWs: WebSocket | null = null;
let stateWsRefs = 0;

export const useLab = create<LabState>((set, get) => ({
  reagents: [], apparatus: [], rulesetVersion: "—", catalogLoaded: false,
  loadCatalog: async () => {
    if (get().catalogLoaded) return;
    try {
      const res = await fetch("/api/v1/bench/catalog");
      if (!res.ok) throw new Error(`catalog HTTP ${res.status}`);
      const data = await res.json() as {
        ruleset_version: string; reagents: ReagentOption[]; apparatus: ApparatusOption[];
      };
      set({ reagents: data.reagents, apparatus: data.apparatus,
            rulesetVersion: data.ruleset_version, catalogLoaded: true });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "目录读取失败" });
    }
  },

  items: [], benchW: 900, benchH: 460,
  selectedId: null, mode: "idle", nearby: null,
  pourSourceId: null, pourTargetId: null, dragId: null, dragOffset: null,
  panelByContainer: {}, selectedPanel: null, loading: false, error: null, opCount: 0,
  wsStatus: "off",

  placeFromRack: (kind, id) => {
    const items = get().items;
    const w = 96, h = 118;
    let x = 40, y = 40;
    for (let tries = 0; tries < 80; tries++) {
      const clash = items.some((it) => rectsOverlap(x, y, w, h, it.x, it.y, it.w, it.h));
      if (!clash) break;
      x += w + 16;
      if (x + w > get().benchW - 20) { x = 40; y += h + 16; }
    }
    let item: BenchItem;
    if (kind === "reagent") {
      const reagent = get().reagents.find((r) => r.compound_id === id);
      if (!reagent) return;
      item = {
        instance_id: nextId("reagent"), apparatus_id: "reagent_bottle", kind: "reagent_bottle",
        label: reagent.label, x, y, w, h, rotation: 0, volume_mL: 250,
        contents: [{ compound_id: reagent.compound_id, concentration_mol_L: reagent.concentration_mol_L, volume_L: 0.25 }],
        reagent, asset: ASSET_URLS.reagent_bottle,
      };
    } else {
      const ap = get().apparatus.find((a) => a.apparatus_id === id);
      if (!ap) return;
      item = {
        instance_id: nextId("vessel"), apparatus_id: ap.apparatus_id, kind: "vessel",
        label: ap.names.zh, x, y, w, h, rotation: 0, volume_mL: 0, contents: [],
        asset: ASSET_URLS[ap.apparatus_id] ?? "/assets/apparatus/beaker_250ml.svg",
      };
    }
    set({ items: [...items, item], selectedId: item.instance_id });
    void get().reportOp("place", { target_instance_id: item.instance_id, payload: { position_mm: { x, y } } });
  },

  startDrag: (instanceId, px, py) => {
    const item = get().items.find((i) => i.instance_id === instanceId);
    if (!item) return;
    set({ mode: "dragging", dragId: instanceId, selectedId: instanceId, nearby: null,
          dragOffset: { dx: px - item.x, dy: py - item.y } });
  },

  moveDrag: (px, py) => {
    const { dragId, items, dragOffset } = get();
    if (!dragId || !dragOffset) return;
    let x = px - dragOffset.dx, y = py - dragOffset.dy;
    x = Math.max(0, Math.min(get().benchW - 96, x));
    y = Math.max(0, Math.min(get().benchH - 118, y));
    const item = items.find((i) => i.instance_id === dragId);
    if (!item) return;
    if (items.some((it) => it.instance_id !== dragId && rectsOverlap(x, y, item.w, item.h, it.x, it.y, it.w, it.h))) return;
    set({ items: items.map((it) => it.instance_id === dragId ? { ...it, x, y } : it) });
  },

  endDrag: () => set({ mode: "idle", dragId: null, dragOffset: null }),

  select: (instanceId) => set({
    selectedId: instanceId,
    selectedPanel: get().panelByContainer[instanceId] ?? null,
  }),

  beginPour: (sourceId, targetId) => set({
    mode: "pouring", pourSourceId: sourceId, pourTargetId: targetId,
    nearby: null, selectedId: sourceId,
  }),

  updatePourTilt: (pointerX, pointerY) => {
    const { pourSourceId, items } = get();
    if (!pourSourceId) return;
    const src = items.find((i) => i.instance_id === pourSourceId);
    if (!src) return;
    const tilt = tiltFromPointer(src.x + src.w / 2, src.y + src.h / 2, pointerX, pointerY);
    set({ items: items.map((it) => it.instance_id === pourSourceId ? { ...it, rotation: tilt } : it) });
  },

  endPour: async () => {
    const { pourSourceId, pourTargetId } = get();
    // 倾倒积分已在 UI 帧循环写入目标 contents（见 BenchView）；此处只回正 + 结算求解
    set({ mode: "idle", pourSourceId: null, pourTargetId: null,
          items: get().items.map((it) => it.rotation ? { ...it, rotation: 0 } : it) });
    if (!pourSourceId || !pourTargetId) return;
    const target = get().items.find((i) => i.instance_id === pourTargetId);
    if (!target || target.contents.length === 0) return;
    set({ loading: true, error: null });
    try {
      const res = await fetch("/api/v1/bench/container-state", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ container_id: pourTargetId, substances: target.contents, addition_order: "acid_into_water" }),
      });
      if (!res.ok) throw new Error(`求解 HTTP ${res.status}`);
      const state = await res.json() as { speciation: SolutionSpeciation; directives: PhenomenonDirective[] };
      const panel = fromSpeciation(state.speciation);
      panel.phenomena = state.directives;
      set((s) => ({
        panelByContainer: { ...s.panelByContainer, [pourTargetId]: panel },
        selectedId: pourTargetId, // 倾倒结束切到接收容器查看结果（符合玩家预期）
        selectedPanel: panel,
        loading: false,
      }));
      await get().reportOp("pour", {
        source_instance_id: pourSourceId, target_instance_id: pourTargetId,
        payload: { transferred_volume_L: target.volume_mL / 1000 },
      });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "倾倒求解失败", loading: false });
    }
  },

  closeItem: (instanceId) => set((s) => ({
    items: s.items.filter((i) => i.instance_id !== instanceId),
    nearby: null,
    selectedId: s.selectedId === instanceId ? null : s.selectedId,
  })),

  clearBench: () => set({ items: [], panelByContainer: {}, selectedPanel: null, nearby: null, error: null }),

  reportOp: async (opType, detail) => {
    try {
      const res = await fetch("/api/v1/bench/operation", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({
          schema_version: "st.operation_event.v1",
          event_id: nextId("evt"), op_type: opType, timestamp_ms: Date.now(), ...detail,
        }),
      });
      if (res.ok) {
        const body = await res.json() as { count: number };
        set({ opCount: body.count });
      }
    } catch { /* 操作计数非关键路径 */ }
  },

  connectWs: () => {
    stateWsRefs += 1;
    set({ wsStatus: stateWs ? "on" : "connecting" });
    if (!stateWs) {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      try {
        const socket = new WebSocket(`${proto}://${location.host}/ws`);
        stateWs = socket;
        socket.onopen = () => {
          for (const it of get().items) {
            socket.send(JSON.stringify({ type: "subscribe", channel: "container_state", container_id: it.instance_id }));
          }
          set({ wsStatus: "on" });
        };
        socket.onmessage = (ev) => {
          try {
            const msg = JSON.parse(String(ev.data)) as {
              type?: string; container_id?: string; speciation?: SolutionSpeciation; directives?: PhenomenonDirective[];
            };
            if (msg.type === "container_state" && msg.container_id && msg.speciation) {
              const panel = fromSpeciation(msg.speciation);
              panel.phenomena = msg.directives ?? [];
              set((s) => ({
                panelByContainer: { ...s.panelByContainer, [msg.container_id!]: panel },
                selectedPanel: s.selectedId === msg.container_id ? panel : s.selectedPanel,
              }));
            }
          } catch { /* 忽略心跳/回显 */ }
        };
        socket.onerror = () => set({ wsStatus: "error" });
        socket.onclose = () => { stateWs = null; set({ wsStatus: "off" }); };
      } catch {
        set({ wsStatus: "error" });
      }
    }
    return () => {
      stateWsRefs = Math.max(0, stateWsRefs - 1);
      if (stateWsRefs === 0 && stateWs) { stateWs.close(); stateWs = null; }
    };
  },
}));

/** 液面层反向旋转角（容器转 θ、液面 −θ 世界水平）。 */
export function liquidRotation(item: BenchItem): number {
  return liquidCounterRotation(item.rotation);
}

/** 填充率。 */
export function itemFill(item: BenchItem): number {
  return fillRatio({ volume_mL: item.volume_mL, tilt_deg: item.rotation }, geometryOf(item));
}

/** 单帧倾倒积分（纯函数出口，供组件帧循环与测试）。 */
export const pourTick = integratePour;
