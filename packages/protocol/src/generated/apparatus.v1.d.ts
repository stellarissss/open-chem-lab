// GENERATED from schemas/apparatus.v1.schema.json — DO NOT EDIT. Run pnpm build:types.

/**
 * 实验台器材：参数单一事实源，驱动 2D SVG/容量/物理约束。路径与 ID 小写 snake_case（01 第六节双平台硬约束）。
 */
export interface Apparatus {
  schema_version: "st.apparatus.v1";
  /**
   * 器材唯一 ID，小写 snake_case
   */
  apparatus_id: string;
  names: BilingualName;
  /**
   * 器材类别（最小集，长线扩类别须升 schema_version）
   */
  type:
    | "beaker"
    | "flask"
    | "test_tube"
    | "burette"
    | "pipette"
    | "graduated_cylinder"
    | "dropper"
    | "stirrer"
    | "hot_plate"
    | "burner"
    | "stand"
    | "tube"
    | "other";
  /**
   * 容量 mL，驱动物理容量约束
   */
  capacity_mL?: number;
  /**
   * 刻度线（mL 值，升序）
   */
  graduations?: number[];
  /**
   * 耐受最高温度 K
   */
  max_temp_K?: number;
  /**
   * 是否可密封（密闭加热后果的前提）
   */
  sealable?: boolean;
  /**
   * 写实 2D 资产引用（tikz-chemlab 输出物路径，见 01 第四节）
   */
  asset?: string;
  physics?: Physics;
  source: Source;
  confidence: Confidence;
  review: Review;
  /**
   * 参数变更版本号，变更须递增
   */
  rule_revision?: number;
}
export interface BilingualName {
  zh: string;
  en: string;
}
/**
 * 物理约束（驱动错误操作后果与现象，近似只作用于表现/时间尺度，不进化学事实层）
 */
export interface Physics {
  wall_thickness_mm?: number;
  /**
   * 是否耐热骤变（炸裂后果前提）
   */
  thermal_shock_sensitive?: boolean;
  /**
   * 最大耐压（密闭后果）
   */
  max_pressure_kPa?: number;
  notes?: string;
}
export interface Source {
  kind: "authoritative_db" | "official_doc" | "literature" | "cameo_fact" | "computed" | "asset_spec";
  ref: string;
  endpoint?: string | null;
  license?: string | null;
  version?: string | null;
  snapshot_date?: string | null;
  sha256?: string | null;
}
export interface Confidence {
  level: "verified" | "extracted" | "crosschecked" | "ml_guess";
  note?: string;
}
export interface Review {
  status: "signed_off" | "pending" | "rejected";
  reviewer?: string | null;
  date?: string | null;
  ai_crosscheck?: string | null;
}
