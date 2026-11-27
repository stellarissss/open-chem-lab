// GENERATED from schemas/report.v1.schema.json — DO NOT EDIT. Run pnpm build:types.

/**
 * 三态出口：定量解 / 覆盖外无明显变化 / 诚实降级
 */
export type Outcome = "solved" | "no_significant_change" | "degraded";

/**
 * 实验报告：操作序列 + 求解快照 + 时间轴曲线 + 反应式 + 来源锚点的只读汇编投影。数值原样取自求解与时间轴产物，不加工、不重算；每条数值以 source_ref 回指来源锚点，三态出口如实呈现。非事实层、不进求解主链。
 */
export interface LabReport {
  schema_version: "st.report.v1";
  /**
   * 内容寻址：由操作序列/快照/曲线/反应式/来源锚点/规则集版本规范化后 sha256 派生，同内容幂等
   */
  report_id: string;
  /**
   * 汇编所用规则集版本，保证可复现
   */
  ruleset_version: string;
  /**
   * 操作序列（取用/倾倒/加入顺序/求解/热效应），按 seq 升序
   */
  operations: Operation[];
  /**
   * 物种快照：一次实验的最终容器状态，outcome 三态如实
   */
  snapshots: Snapshot[];
  /**
   * 时间轴曲线原值（物种/物理量 -> [timestamp_ms, value]）
   */
  curves: Curve[];
  /**
   * 反应式：逐条引用已签核 reaction_rule，不手写虚构方程式
   */
  reactions: Reaction[];
  /**
   * 来源锚点：每条数值 source_ref 指向本数组 source_id
   *
   * @minItems 1
   */
  sources: [SourceAnchor, ...SourceAnchor[]];
  outcome_summary: OutcomeSummary;
}
export interface Operation {
  /**
   * 操作序号（时序由序号表达，不用墙钟时间以保证幂等）
   */
  seq: number;
  kind: "place_apparatus" | "pour" | "set_order" | "solve" | "heat";
  container_id: string;
  apparatus_id?: string;
  compound_id?: string;
  concentration_mol_L?: number;
  volume_L?: number;
  addition_order?: "water_into_acid" | "acid_into_water";
}
export interface Snapshot {
  container_id: string;
  outcome: Outcome;
  /**
   * 求解活度口径 pH 原值
   */
  ph?: number;
  ionic_strength?: number;
  temperature_K?: number;
  /**
   * 降级出口置信度
   */
  confidence?: number;
  /**
   * 非 solved 出口的诚实原因
   */
  reason?: string;
  species?: SpeciesValue[];
  /**
   * 指向 sources[].source_id
   */
  source_ref: string;
}
export interface SpeciesValue {
  /**
   * 物种名（引用事实层标识）
   */
  name: string;
  concentration_mol_l: number;
  phase?: string;
  /**
   * 指向 sources[].source_id
   */
  source_ref: string;
}
export interface Curve {
  /**
   * 物种名或 ph 等物理量
   */
  species: string;
  /**
   * 时间轴原值，不插值不加工
   */
  points: [number, number][];
  /**
   * 指向 sources[].source_id
   */
  source_ref: string;
}
export interface Reaction {
  /**
   * 已签核 reaction_rule 的 rule_id
   */
  rule_id: string;
  /**
   * 取自规则 reaction.equation 原值，不手写
   */
  equation: string;
  data_class?: string;
  confidence_level?: string;
  /**
   * 指向 sources[].source_id（权威源快照哈希锚点）
   */
  source_ref: string;
}
export interface SourceAnchor {
  source_id: string;
  kind: "solver" | "timeline" | "ruleset" | "authoritative_db" | "crosscheck" | "computed";
  /**
   * 求解器/数据源/时间轴标识
   */
  ref: string;
  /**
   * 权威源快照或规则集哈希锚点；无则 null
   */
  sha256?: string | null;
  version?: string | null;
  snapshot_date?: string | null;
  note?: string;
}
export interface OutcomeSummary {
  solved: number;
  no_significant_change: number;
  degraded: number;
  total: number;
}
