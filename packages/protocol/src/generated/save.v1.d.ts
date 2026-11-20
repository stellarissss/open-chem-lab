// GENERATED from schemas/save.v1.schema.json — DO NOT EDIT. Run pnpm build:types.

/**
 * 轻量存档：实验台上的器材与物质摆布 + 时间轴引用 + 规则集版本。刻意不含网格/RLE/多人协作/Yjs。
 */
export interface SaveGame {
  schema_version: "st.save.v1";
  save_id: string;
  /**
   * 规则集版本，存档回放必须用同版规则集以保证数值可复现
   */
  ruleset_version: string;
  /**
   * 实验台器材摆布（位置/朝向/连接关系，坐标由表现层定义）
   */
  apparatus: ApparatusPlacement[];
  /**
   * 已取用物质（引用 content 中的物质 ID，不内联虚构数据）
   */
  substances: SubstanceRef[];
  /**
   * 关联的时间轴快照引用；null 表示尚未产生时间轴
   */
  timeline_ref?: string | null;
  created_at: string;
}
export interface ApparatusPlacement {
  placement_id: string;
  /**
   * 引用 apparatus 实体的 ID
   */
  apparatus_id: string;
  x: number;
  y: number;
  rotation_deg?: number;
  /**
   * 导管等连接关系（对端 placement_id）
   */
  connections?: string[];
}
export interface SubstanceRef {
  /**
   * 引用 content 中的真实物质 ID
   */
  compound_id: string;
  /**
   * 所在器材摆位 ID
   */
  placement_id: string;
  /**
   * 取用量（单位由物质卡定义）
   */
  amount?: number;
}
