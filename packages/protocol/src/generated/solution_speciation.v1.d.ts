// GENERATED from schemas/solution_speciation.v1.schema.json — DO NOT EDIT. Run pnpm build:types.

/**
 * 每容器隐藏化学态：不可见反应也真实发生。物种分布 + pH + 离子强度 + 平衡 + 隐藏反应。由求解层（spec-003+）产出，本切片只定义契约。
 */
export interface SolutionSpeciation {
  schema_version: "st.solution_speciation.v1";
  /**
   * 快照唯一 ID，供幂等与回放
   */
  speciation_id: string;
  /**
   * 对应实验台容器摆位 ID
   */
  container_id: string;
  /**
   * 物种分布（浓度/活度/摩尔分数）
   */
  species: SpeciesConcentration[];
  /**
   * pH 值（求解结果）
   */
  ph: number;
  /**
   * 求解出口语义：区分已求解、条件外无变化与诚实降级，避免把数值失败表述为科学结论
   */
  outcome?: "solved" | "no_significant_change" | "degraded";
  /**
   * 降级出口的置信度（outcome=degraded 时给出），表现层据此提示
   */
  confidence?: number;
  /**
   * 非 solved 出口的诚实原因（如覆盖外物质、活度越界、数值不收敛）；solved 时不给出。兑现 spec-003 降级附原因的承诺
   */
  reason?: string;
  /**
   * 离子强度 mol/L
   */
  ionic_strength: number;
  /**
   * 氧化还原电位 pe（可选）
   */
  pe?: number;
  temperature_K?: number;
  /**
   * 生效平衡引用（指向 reaction_rule ID）
   */
  equilibria?: string[];
  /**
   * 隐藏反应（不可见但真实发生，引用 reaction_rule ID）
   */
  hidden_reactions?: string[];
  /**
   * 本体系实际加入的指示剂 compound_id 列表；仅对这些指示剂派生变色现象（倒什么看什么）
   */
  indicators?: string[];
  /**
   * 错误操作后果的物理提示（如放热飞溅），供表现层与面板显示
   */
  physics_note?: string;
  /**
   * 求解所用规则集版本，保证可复现
   */
  ruleset_version: string;
  /**
   * 相对仿真起点毫秒（时间轴对齐）
   */
  timestamp_ms?: number;
  source?: Source;
}
export interface SpeciesConcentration {
  /**
   * 物种 ID（如 H+ / OH- / CH3COO-）
   */
  species_id: string;
  /**
   * 摩尔浓度 mol/L
   */
  concentration_mol_L: number;
  /**
   * 活度（可选，求解器给出）
   */
  activity?: number;
  /**
   * 摩尔分数（可选）
   */
  mole_fraction?: number;
}
export interface Source {
  kind: "solver" | "authoritative_db" | "computed";
  /**
   * 求解器/数据源标识
   */
  ref: string;
  version?: string | null;
  snapshot_date?: string | null;
}
