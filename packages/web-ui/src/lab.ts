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

export interface LabState {
  system: ScanSystem;
  timeline: SpeciationTimeline | null;
  frameIndex: number;
  playing: boolean;
  loading: boolean;
  error: string | null;
  live: PanelData | null;
  loadTimeline: (system: ScanSystem) => Promise<void>;
  setSystem: (system: ScanSystem) => void;
  setFrame: (index: number) => void;
  togglePlay: () => void;
  solveLive: (substances: SubstanceInput[]) => Promise<void>;
  clearLive: () => void;
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
}));
