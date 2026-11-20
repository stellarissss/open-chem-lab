// GENERATED from schemas/timeline.v1.schema.json — DO NOT EDIT. Run pnpm build:types.

/**
 * 关键快照时间轴：隐藏化学态每帧变化的稀疏快照 + 曲线。物种面板与时间轴回放的数据来源。事实层数据（非表现）。
 */
export interface SpeciationTimeline {
  schema_version: "st.timeline.v1";
  timeline_id: string;
  ruleset_version: string;
  /**
   * 按时间升序的关键帧快照
   */
  keyframes: Keyframe[];
  /**
   * 按物种/物理量聚合的连续曲线（可选，回放时可插值）
   */
  curves?: Curve[];
}
export interface Keyframe {
  timestamp_ms: number;
  container_id: string;
  speciation: SpeciationSnapshot;
}
/**
 * 每容器隐藏化学态快照（solution_speciation 的投影）
 */
export interface SpeciationSnapshot {
  ph: number;
  ionic_strength?: number;
  species?: {
    /**
     * 物种名（引用事实层标识）
     */
    name: string;
    concentration_mol_l: number;
    /**
     * aq/s/g 等相态
     */
    phase?: string;
  }[];
  [k: string]: unknown;
}
export interface Curve {
  species: string;
  points: [number, number][];
}
