import { create } from "zustand";
import type {
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
}

export const SYSTEM_LABELS: Record<ScanSystem, string> = {
  strong: "强酸—强碱滴定",
  weak: "弱酸—强碱滴定",
};

export const useLab = create<LabState>((set, get) => ({
  system: "strong",
  timeline: null,
  frameIndex: 0,
  playing: false,
  loading: false,
  error: null,
  live: null,
  heat: null,

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
      set({ heat, loading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "热效应求解失败", loading: false });
    }
  },
}));
