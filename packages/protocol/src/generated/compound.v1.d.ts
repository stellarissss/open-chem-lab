// GENERATED from schemas/compound.v1.schema.json — DO NOT EDIT. Run pnpm build:types.

/**
 * 可玩物质卡：凡入库必须可玩。数据分 fact（计量/物性，零错签核）/ presentation（颜色/外观，可标来源夸张）/ safety（GHS 危害，严谨签核）三层。护栏字段保证来源/置信度/对拍/签核完整，非 verified 不进可玩层。
 */
export interface Compound {
  schema_version: "st.compound.v1";
  /**
   * 物质唯一 ID，小写 snake_case（双平台硬约束，见 01 第六节）
   */
  compound_id: string;
  names: BilingualName;
  /**
   * 化学式（如 HCl / CH3COOH / NH3·H2O），唯一标识化学身份
   */
  formula: string;
  /**
   * CAS 登记号，可选但推荐（构建期从 PubChem 快照取）
   */
  cas_number?: string | null;
  /**
   * 该卡主数据类型：fact 零错 / presentation 可标来源夸张 / safety 严谨签核
   */
  data_class: "fact" | "presentation" | "safety";
  properties?: CompoundProperties;
  safety?: Safety;
  presentation?: Presentation;
  reagent_solution?: ReagentSolution;
  source: Source;
  confidence: Confidence;
  review: Review;
  /**
   * 参数变更版本号；变更须递增而非原地覆盖，支持回滚
   */
  rule_revision?: number;
  /**
   * 凡入库物质必须可玩（01 第二节）；非 verified 不得置 true
   */
  playable: true;
}
export interface BilingualName {
  /**
   * 中文名
   */
  zh: string;
  /**
   * 英文名
   */
  en: string;
  /**
   * 常用别名（如醋酸/乙酸）
   */
  common?: string;
}
/**
 * 物性事实（fact 层），须零错签核；字段按需要扩展，禁止凭记忆写数值
 */
export interface CompoundProperties {
  /**
   * 摩尔质量 g/mol
   */
  molar_mass_g_mol?: number;
  /**
   * 密度 g/mL（标注温度条件）
   */
  density_g_ml?: number;
  /**
   * 酸解离常数 pKa（25°C，仅弱酸填）
   */
  pka?: number;
  /**
   * 碱解离常数 pKb（25°C，仅弱碱填）
   */
  pkb?: number;
  /**
   * pKa 说明（强电解质为何不填有限值等）
   */
  pka_note?: string;
  /**
   * pKb 说明
   */
  pkb_note?: string;
  /**
   * pKa 来源追溯（权威数据库反应行）
   */
  pka_source?: string;
  /**
   * pKb 来源追溯
   */
  pkb_source?: string;
  /**
   * 是否弱酸
   */
  weak_acid?: boolean;
  /**
   * 是否弱碱
   */
  weak_base?: boolean;
  /**
   * 是否强电解质（完全解离，不设有限 pKa/Kb）
   */
  strong_electrolyte?: boolean;
  /**
   * 溶解性描述或定量值（带条件）
   */
  solubility?: string;
  /**
   * 物性参考温度 K，默认 298.15（25°C）
   */
  reference_temp_K?: number;
}
/**
 * GHS 危害（safety 层），严谨签核，驱动错误操作后果
 */
export interface Safety {
  /**
   * GHS 危险公示码（如 H302）/ 象形图代码
   */
  ghs_codes?: string[];
  /**
   * 警示词
   */
  signal_word?: "danger" | "warning" | "none";
  /**
   * 危害说明（如腐蚀性、遇水放热）
   */
  hazard_notes?: string;
  source?: Source;
}
/**
 * 来源链：kind + ref 必填；权威衍生需带 version/snapshot_date/sha256
 */
export interface Source {
  /**
   * 来源类别；cameo_fact 为隔离仓事实性结论，computed 为对拍推导
   */
  kind: "authoritative_db" | "official_doc" | "literature" | "cameo_fact" | "computed";
  /**
   * 来源标识（数据库名/文档/URL/DOI）
   */
  ref: string;
  /**
   * 取数 endpoint（构建期快照来源）
   */
  endpoint?: string | null;
  /**
   * 数据许可（CC-BY-SA 衍生须标）
   */
  license?: string | null;
  /**
   * 数据源版本
   */
  version?: string | null;
  /**
   * 快照日期 ISO-8601
   */
  snapshot_date?: string | null;
  /**
   * 快照 sha256，保证可追溯与可回滚
   */
  sha256?: string | null;
}
/**
 * 外观表现（presentation 层），可夸张但必须标来源，不受零错红线约束
 */
export interface Presentation {
  /**
   * 外观描述（如无色透明液体）
   */
  appearance?: string;
  /**
   * 溶液颜色（表现层显示值）
   */
  solution_color?: string;
  indicator?: Indicator;
  notes?: string;
}
/**
 * 指示剂响应：表现层按求解 pH 用 Henderson–Hasselbalch 连续混色，现象由状态派生而非逐反应手写
 */
export interface Indicator {
  /**
   * 指示剂酸解离常数 pKa（25°C），fact 层零错签核
   */
  pka: number;
  /**
   * 酸式色（pH < pKa−1 时的显示颜色，如 red / colorless）
   */
  acid_color: string;
  /**
   * 碱式色（pH > pKa+1 时的显示颜色，如 yellow / pink）
   */
  base_color: string;
  /**
   * 来源与观测说明
   */
  note?: string;
}
/**
 * 试剂瓶标签浓度（008）：玩家从试剂架取用的瓶装溶液初始条件，非求解结果——故不违反诚实计算红线，但须来源锚定并经用户签核。仅可瓶装可玩物质填写；纯水等溶剂型物质以 solvent 标记、浓度仅作参考。
 */
export interface ReagentSolution {
  /**
   * 瓶装溶液标称浓度 mol/L（操作初始条件，非计算值）
   */
  concentration_mol_L: number;
  /**
   * 是否溶剂型（如蒸馏水）；浓度仅参考，求解按溶剂特例处理
   */
  solvent?: boolean;
  /**
   * 是否危险试剂（如浓硫酸）；走热效应/后果写实路径，不进稀区主求解
   */
  hazard?: boolean;
  /**
   * 适用范围/注意事项（如浓区体系、仅供滴加）
   */
  applicability?: string;
  /**
   * 浓度来源：实验室常规试剂规格 + 用户签核日期
   */
  source: string;
}
export interface Confidence {
  /**
   * verified=用户签核进可玩层；extracted=候选池；crosschecked=AI 对拍；ml_guess=禁用（门禁拒绝）
   */
  level: "verified" | "extracted" | "crosschecked" | "ml_guess";
  /**
   * 置信度说明
   */
  note?: string;
}
export interface Review {
  /**
   * 签核状态；仅 signed_off 允许 playable=true
   */
  status: "signed_off" | "pending" | "rejected";
  /**
   * 签核人（用户）
   */
  reviewer?: string | null;
  /**
   * 签核日期 ISO-8601
   */
  date?: string | null;
  /**
   * AI 独立对拍记录路径（指向 content/ai-crosscheck/）
   */
  ai_crosscheck?: string | null;
}
