// GENERATED from schemas/reaction_rule.v1.schema.json — DO NOT EDIT. Run pnpm build:types.

/**
 * 条件化真实反应（核心事实层）。定量 equilibrium/kinetics/thermo + 适用条件 applicability + 数值护栏 numerics + 现象 effects + 来源/置信度/对拍/签核 完整。计量守恒、条件互斥（同一反应物集合+条件不得有两条 verified）、applicability 必填、ml_guess 禁用。参数变更走 rule_revision 禁原地覆盖。
 */
export interface ReactionRule {
  schema_version: "st.reaction_rule.v1";
  /**
   * 规则唯一 ID，小写 snake_case
   */
  rule_id: string;
  /**
   * 所属化学体系（如 neutralization），对应 content/rules/ 子目录名
   */
  system?: string;
  reaction: Reaction;
  equilibrium?: Equilibrium;
  kinetics?: Kinetics;
  thermo?: Thermo;
  applicability: Applicability;
  numerics?: Numerics;
  /**
   * 关联现象 ID（指向 phenomenon 注册表，表现层按 ID 渲染，不进化学事实层）
   */
  effects?: string[];
  /**
   * 反应规则主数据类型；数值规则须为 fact
   */
  data_class: "fact" | "presentation" | "safety";
  source: Source;
  confidence: Confidence;
  ai_crosscheck: AiCrosscheck;
  review: Review;
  /**
   * 规则修订号，参数变更须递增而非原地覆盖，支持回滚
   */
  rule_revision: number;
}
/**
 * 反应计量。reactants/products 均为 species 计量映射，供计量守恒校验（RDKit/CI）
 */
export interface Reaction {
  /**
   * 人类可读反应式（如 H+ + OH- = H2O）
   */
  equation?: string;
  /**
   * 反应物 -> 计量系数（正数）
   */
  reactants: {
    [k: string]: number;
  };
  /**
   * 产物 -> 计量系数（正数）
   */
  products: {
    [k: string]: number;
  };
  /**
   * 反应物净电荷，供电荷守恒校验
   */
  net_charge_reactants?: number;
  /**
   * 产物净电荷，供电荷守恒校验
   */
  net_charge_products?: number;
}
/**
 * 平衡定量（至少提供 log_k 或 delta_g_kj 之一用于平衡求解）
 */
export interface Equilibrium {
  /**
   * 25°C 平衡常数 log10 K
   */
  log_k_25C?: number;
  /**
   * 标准吉布斯自由能变 kJ/mol
   */
  delta_g_kj_mol?: number;
  /**
   * 标准焓变 kJ/mol
   */
  delta_h_kj_mol?: number;
  /**
   * PHREEQC -analytic/-analytical 温度系数 A1..A6（如有）
   */
  analytic_expression?: number[];
  /**
   * 温度系数说明（随求解层接入）
   */
  analytic_note?: string;
  /**
   * 常数参考温度 K
   */
  temperature_K?: number;
}
/**
 * 动力学定量（可选；中和等快反应用平衡描述，慢反应填此节）
 */
export interface Kinetics {
  /**
   * 速率方程表达式
   */
  rate_law?: string;
  /**
   * Arrhenius 指前因子
   */
  a_arrhenius?: number;
  /**
   * 活化能 kJ/mol
   */
  ea_kj_mol?: number;
  /**
   * 25°C 速率常数
   */
  rate_constant_25C?: number;
  /**
   * true=瞬时平衡，无需动力学积分（中和反应）
   */
  fast_equilibrium?: boolean;
  /**
   * 动力学说明
   */
  note?: string;
}
/**
 * 热效应（驱动温度变化现象，数值进 fact 层）
 */
export interface Thermo {
  /**
   * 反应焓变 kJ/mol（放热为负）
   */
  delta_h_kj_mol?: number;
  /**
   * 是否放热
   */
  exothermic?: boolean;
  notes?: string;
}
/**
 * 适用条件（必填）。条件互斥护栏：同一反应物集合 + 条件组合不得有两条 verified 规则
 */
export interface Applicability {
  /**
   * 适用条件列表（如 aqueous_25C、ph_range）
   *
   * @minItems 1
   */
  conditions: [string, ...string[]];
  /**
   * 适用 pH 区间 [min, max]
   *
   * @minItems 2
   * @maxItems 2
   */
  ph_range?: [number, number];
  /**
   * 适用温度区间 [min, max] K
   *
   * @minItems 2
   * @maxItems 2
   */
  temp_range_K?: [number, number];
  /**
   * 排除条件
   */
  excludes?: string[];
}
/**
 * 数值护栏：rtol/atol 由求解器决定，此处只标注数值稳定性约束，禁硬编码时间阈值（01 第四节）
 */
export interface Numerics {
  /**
   * 相对容差
   */
  rtol?: number;
  /**
   * 绝对容差
   */
  atol?: number;
  /**
   * 是否刚性（提示 LSODA/BDF 切换）
   */
  stiff?: boolean;
  /**
   * 数值护栏说明
   */
  note?: string;
  notes?: string;
}
export interface Source {
  kind: "authoritative_db" | "official_doc" | "literature" | "cameo_fact" | "computed" | "ord_derived";
  ref: string;
  endpoint?: string | null;
  /**
   * ord_derived 须标 CC-BY-SA 溯源
   */
  license?: string | null;
  version?: string | null;
  snapshot_date?: string | null;
  sha256?: string | null;
}
export interface Confidence {
  /**
   * ml_guess 门禁拒绝
   */
  level: "verified" | "extracted" | "crosschecked" | "ml_guess";
  note?: string;
}
/**
 * AI 独立对拍记录（权威源→对拍→签核链的一环）
 */
export interface AiCrosscheck {
  /**
   * 对拍方法（如 analytic_25C / chempy / phreeqpython）
   */
  method: string;
  /**
   * 对拍记录文件路径
   */
  record_path?: string | null;
  /**
   * 对拍期望值（如 pH、浓度），键由体系定义
   */
  expected_values?: {
    [k: string]: unknown;
  };
  note?: string;
}
export interface Review {
  status: "signed_off" | "pending" | "rejected";
  reviewer?: string | null;
  date?: string | null;
  note?: string;
}
