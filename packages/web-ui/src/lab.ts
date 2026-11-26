import { create } from "zustand";
import type {
  LabReport,
  Operation,
  PhenomenonDirective,
  SolutionSpeciation,
  SpeciationSnapshot,
  SpeciationTimeline,
} from "@st/protocol";

// 唯一取数口：/api/* 全部经 gateway；web-ui 不直连求解库（01 第六节依赖规则）。

export type ScanSystem = "strong" | "weak";

export interface SpeciesRow {
  name: string;
  concentration: number;
  activity?: number;
  moleFraction?: number;
  phase?: string;
}

/** 面板统一视图模型：兼容完整 solution_speciation 与时间轴关键帧投影。 */
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

interface SnapshotExtra {
  outcome?: string;
  confidence?: number;
  reason?: string;
  temperature_K?: number;
  hidden_reactions?: string[];
  phenomena?: PhenomenonDirective[];
  timestamp_ms?: number;
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

export function fromSnapshot(snapshot: SpeciationSnapshot, containerId: string): PanelData {
  const s = snapshot as SpeciationSnapshot & SnapshotExtra;
  return {
    containerId,
    ph: s.ph,
    ionicStrength: s.ionic_strength ?? 0,
    temperatureK: s.temperature_K,
    outcome: s.outcome ?? "solved",
    confidence: s.confidence,
    reason: s.reason,
    species: (s.species ?? []).map((row) => ({
      name: row.name,
      concentration: row.concentration_mol_l,
      phase: row.phase,
    })),
    hiddenReactions: s.hidden_reactions ?? [],
    phenomena: s.phenomena ?? [],
    timestampMs: s.timestamp_ms,
  };
}

export interface SubstanceInput {
  compound_id: string;
  concentration_mol_L: number;
  volume_L: number;
}

/** 错误操作后果热结果（spec-005 飞溅链路）：物理量 + 派生现象指令。 */
export interface HeatResult {
  outcome: string;
  delta_T_K?: number;
  final_temperature_K?: number;
  splash_risk?: boolean;
  addition_order?: string;
  heat_released_kj?: number;
  hazard?: string;
  directives: PhenomenonDirective[];
}

export type AdditionOrder = "water_into_acid" | "acid_into_water";

/** 实验台可取的药品（引用 content 中已签核可玩物质；id 与 ruleset compound_id 对齐）。 */
export interface ReagentOption {
  compound_id: string;
  label: string;
  default_concentration_mol_L: number;
  /** 浓硫酸为危险试剂，走 /api/v1/heat 专用路径，不进稀区主求解。 */
  hazard?: boolean;
}

export const REAGENTS: ReagentOption[] = [
  { compound_id: "hcl", label: "盐酸 HCl", default_concentration_mol_L: 0.1 },
  { compound_id: "naoh", label: "氢氧化钠 NaOH", default_concentration_mol_L: 0.1 },
  { compound_id: "acetic_acid", label: "乙酸 CH₃COOH", default_concentration_mol_L: 0.1 },
  { compound_id: "koh", label: "氢氧化钾 KOH", default_concentration_mol_L: 0.1 },
  { compound_id: "phenolphthalein", label: "酚酞（指示剂）", default_concentration_mol_L: 0.001 },
  { compound_id: "methyl_orange", label: "甲基橙（指示剂）", default_concentration_mol_L: 0.001 },
  { compound_id: "sulfuric_acid_conc", label: "浓硫酸 H₂SO₄（危险）", default_concentration_mol_L: 18.4, hazard: true },
  { compound_id: "water", label: "蒸馏水 H₂O", default_concentration_mol_L: 1.0 },
];

/** 实验台摆放的一件器材（apparatus 单一事实源引用的运行时实例）。 */
export interface ApparatusSlot {
  slot_id: string;
  apparatus_id: string;
  label: string;
  x: number;
  y: number;
  /** 当前容器内的物质（倾倒追加）。 */
  contents: SubstanceInput[];
}

/** 现象来源：live 求解 / WS 推送 / 时间轴回放。三者走同一渲染管线。 */
export type PhenomenonSource = "none" | "live" | "ws" | "timeline";

export interface LabState {
  system: ScanSystem;
  timeline: SpeciationTimeline | null;
  frameIndex: number;
  playing: boolean;
  loading: boolean;
  error: string | null;
  live: PanelData | null;
  heat: HeatResult | null;
  loadTimeline: (system: ScanSystem) => Promise<void>;
  setSystem: (system: ScanSystem) => void;
  setFrame: (index: number) => void;
  togglePlay: () => void;
  solveLive: (substances: SubstanceInput[]) => Promise<void>;
  clearLive: () => void;
  solveHeat: (order: AdditionOrder) => Promise<void>;
  // spec-005 装置建造 + WS 现象下发
  slots: ApparatusSlot[];
  selectedReagent: string;
  selectedVolume_L: number;
  additionOrder: AdditionOrder;
  phenomenonSource: PhenomenonSource;
  wsStatus: "off" | "connecting" | "on" | "error";
  wsDirectives: PhenomenonDirective[];
  setSelectedReagent: (id: string) => void;
  setSelectedVolume: (v: number) => void;
  setAdditionOrder: (o: AdditionOrder) => void;
  placeApparatus: (apparatus_id: string, label: string) => void;
  pourInto: (slot_id: string) => Promise<void>;
  clearBench: () => void;
  connectWs: () => () => void;
  // spec-006 实验报告：操作序列记录 + 经 gateway 取 solver-worker 汇编的只读报告
  operations: Operation[];
  report: LabReport | null;
  generateReport: () => Promise<void>;
  clearReport: () => void;
}

/** 追加一条操作记录；序号由当前长度派生，不用墙钟时间以保证报告幂等。 */
function appendOp(ops: Operation[], op: Omit<Operation, "seq">): Operation[] {
  return [...ops, { seq: ops.length + 1, ...op } as Operation];
}

export const SYSTEM_LABELS: Record<ScanSystem, string> = {
  strong: "强酸—强碱滴定",
  weak: "弱酸—强碱滴定",
};

/** WS phenomenon 单例：StrictMode 双挂载下避免误关连接（模块级，非 store 状态）。 */
let phenomWs: WebSocket | null = null;
let phenomWsRefs = 0;

export const useLab = create<LabState>((set, get) => ({
  system: "strong",
  timeline: null,
  frameIndex: 0,
  playing: false,
  loading: false,
  error: null,
  live: null,
  heat: null,
  // spec-005 装置建造初始态：台上预置一只烧杯（容量来自 apparatus 事实源 beaker_250ml）。
  slots: [{ slot_id: "beaker-1", apparatus_id: "beaker_250ml", label: "烧杯 250 mL",
            x: 0, y: 0, contents: [] }],
  selectedReagent: "naoh",
  selectedVolume_L: 0.5,
  additionOrder: "acid_into_water",
  phenomenonSource: "none",
  wsStatus: "off",
  wsDirectives: [],
  operations: [],
  report: null,

  setSelectedReagent: (id) => set({ selectedReagent: id }),
  setSelectedVolume: (v) => set({ selectedVolume_L: v }),
  setAdditionOrder: (o) => set({ additionOrder: o }),

  placeApparatus: (apparatus_id, label) => {
    const slots = get().slots;
    const slot_id = `${apparatus_id}-${slots.length + 1}`;
    set({
      slots: [...slots, { slot_id, apparatus_id, label, x: 0, y: 0, contents: [] }],
      operations: appendOp(get().operations, { kind: "place_apparatus", container_id: slot_id, apparatus_id }),
    });
  },

  clearBench: () => set({
    slots: [{ slot_id: "beaker-1", apparatus_id: "beaker_250ml", label: "烧杯 250 mL",
              x: 0, y: 0, contents: [] }],
    live: null, heat: null, phenomenonSource: "none", wsDirectives: [],
    operations: [], report: null,
  }),

  /** 倾倒：把当前选中药品按体积加入目标容器，再经 gateway 求解，同步更新现象与物种面板。 */
  pourInto: async (slot_id) => {
    const { slots, selectedReagent, selectedVolume_L, additionOrder } = get();
    const reagent = REAGENTS.find((r) => r.compound_id === selectedReagent);
    if (!reagent) return;
    const added: SubstanceInput = {
      compound_id: reagent.compound_id,
      concentration_mol_L: reagent.default_concentration_mol_L,
      volume_L: selectedVolume_L,
    };
    const target = slots.find((s) => s.slot_id === slot_id);
    const contents = [...(target?.contents ?? []), added];
    set({
      slots: slots.map((s) => s.slot_id === slot_id ? { ...s, contents } : s),
      operations: appendOp(get().operations, {
        kind: "pour", container_id: slot_id, compound_id: reagent.compound_id,
        concentration_mol_L: reagent.default_concentration_mol_L, volume_L: selectedVolume_L,
        ...(reagent.hazard ? { addition_order: additionOrder } : {}),
      }),
      loading: true, error: null,
    });

    const hasHazard = contents.some((s) => REAGENTS.find((r) => r.compound_id === s.compound_id)?.hazard);
    try {
      if (hasHazard) {
        // 浓硫酸走热效应专用路径（稀区主求解对浓酸返回 no_significant_change）。
        const body = { container_id: slot_id, addition_order: additionOrder, substances: contents };
        const res = await fetch("/api/v1/heat", {
          method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const heat = (await res.json()) as HeatResult;
        set({ heat, loading: false, phenomenonSource: "live" });
      } else {
        const body = { container_id: slot_id, substances: contents };
        const [specRes, phenRes] = await Promise.all([
          fetch("/api/v1/speciation", {
            method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
          }),
          fetch("/api/v1/speciation/phenomena", {
            method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
          }),
        ]);
        if (!specRes.ok) throw new Error(`求解 HTTP ${specRes.status}`);
        const spec = (await specRes.json()) as SolutionSpeciation;
        const data = fromSpeciation(spec);
        if (phenRes.ok) data.phenomena = (await phenRes.json()) as PhenomenonDirective[];
        set({ live: data, heat: null, loading: false, phenomenonSource: "live" });
      }
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "倾倒求解失败", loading: false });
    }
  },

  /** 订阅 gateway 的 WS phenomenon 通道；返回的清理函数按引用计数释放连接。 */
  connectWs: () => {
    // 模块级单例：React StrictMode 会双挂载，引用计数避免第一次 cleanup 误关
    // 第二次挂载正要使用的连接（否则出现 "closed before established"）。
    phenomWsRefs += 1;
    set({ wsStatus: phenomWs ? "on" : "connecting" });
    if (!phenomWs) {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      try {
        const socket = new WebSocket(`${proto}://${location.host}/ws`);
        phenomWs = socket;
        socket.onopen = () => {
          socket.send(JSON.stringify({ type: "subscribe", channel: "phenomenon" }));
          set({ wsStatus: "on" });
        };
        socket.onmessage = (ev) => {
          try {
            const msg = JSON.parse(String(ev.data)) as {
              type?: string; directives?: PhenomenonDirective[];
            };
            if (msg.type === "phenomenon" && Array.isArray(msg.directives)) {
              set({ wsDirectives: msg.directives, phenomenonSource: "ws" });
            }
          } catch { /* 忽略非 JSON 心跳/回显 */ }
        };
        socket.onerror = () => set({ wsStatus: "error" });
        socket.onclose = () => { phenomWs = null; set({ wsStatus: "off" }); };
      } catch {
        set({ wsStatus: "error" });
      }
    }
    return () => {
      phenomWsRefs = Math.max(0, phenomWsRefs - 1);
      if (phenomWsRefs === 0 && phenomWs) {
        phenomWs.close();
        phenomWs = null;
      }
    };
  },

  loadTimeline: async (system) => {
    set({ loading: true, error: null });
    try {
      const res = await fetch(`/api/v1/timeline?system=${encodeURIComponent(system)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const timeline = (await res.json()) as SpeciationTimeline;
      set({ timeline, frameIndex: 0, playing: false, loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "时间轴读取失败", loading: false });
    }
  },

  setSystem: (system) => {
    set({ system, live: null });
    void get().loadTimeline(system);
  },

  setFrame: (index) => {
    const total = get().timeline?.keyframes.length ?? 0;
    set({ frameIndex: Math.max(0, Math.min(total - 1, index)) });
  },

  togglePlay: () => set((state) => ({ playing: !state.playing })),

  solveLive: async (substances) => {
    set({ loading: true, error: null });
    const body = { container_id: "live-beaker", substances };
    try {
      const [specRes, phenRes] = await Promise.all([
        fetch("/api/v1/speciation", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(body),
        }),
        fetch("/api/v1/speciation/phenomena", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(body),
        }),
      ]);
      if (!specRes.ok) throw new Error(`求解 HTTP ${specRes.status}`);
      const spec = (await specRes.json()) as SolutionSpeciation;
      const data = fromSpeciation(spec);
      if (phenRes.ok) data.phenomena = (await phenRes.json()) as PhenomenonDirective[];
      set({ live: data, loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "求解失败", loading: false });
    }
  },

  clearLive: () => set({ live: null }),

  solveHeat: async (order) => {
    set({ loading: true, error: null });
    // 浓硫酸 18.4M × 54.4mL ≈ 1mol + 水 1L（与已签核黄金用例同形）。
    const body = {
      container_id: "hazard-beaker",
      addition_order: order,
      substances: [
        { compound_id: "sulfuric_acid_conc", concentration_mol_L: 18.4, volume_L: 0.0544 },
        { compound_id: "water", concentration_mol_L: 1.0, volume_L: 1.0 },
      ],
    };
    try {
      const res = await fetch("/api/v1/heat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const heat = (await res.json()) as HeatResult;
      // 与 pourInto 的危害分支同源：显式标记 live，飞溅渲染不依赖 WS 恰好连上。
      set({ heat, loading: false, phenomenonSource: "live" });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "热效应求解失败", loading: false });
    }
  },

  /** 生成只读报告：把操作序列 + 实验台当前物质组合经 gateway 提交，由 solver-worker 汇编；数值不在此层加工。 */
  generateReport: async () => {
    const { operations, slots, system } = get();
    // 以实验台现状（所有容器物质汇总）作为报告求解输入，保证数值来自真实状态。
    const substances = slots.flatMap((s) => s.contents);
    set({ loading: true, error: null });
    try {
      const res = await fetch("/api/v1/report", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ operations, substances, system, container_id: "report-beaker" }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const built = (await res.json()) as LabReport;
      set({ report: built, loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "报告生成失败", loading: false });
    }
  },

  clearReport: () => set({ report: null }),
}));
