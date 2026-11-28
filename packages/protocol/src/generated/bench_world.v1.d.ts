// GENERATED from schemas/bench_world.v1.schema.json — DO NOT EDIT. Run pnpm build:types.

/**
 * st.bench_world.v1 — 自由写实台面的世界状态（008）：器材实例/位置/倾角/容器内容。前端权威、网关与求解侧按需订阅。器材与试剂瓶统一为可摆放容器实例；一切数值由操作与求解产生、无预设配比。
 */
export interface BenchWorld {
  schema_version: "st.bench_world.v1";
  /**
   * 台面唯一 ID（单机单台面，预留多实例）
   */
  bench_id: string;
  /**
   * 台上所有器材实例（含试剂瓶，统一为可摆放容器）
   */
  apparatus_instances: ApparatusInstance[];
  bench_bounds: BenchBounds;
  /**
   * 本台面对应的物化 ruleset 版本（事实层对齐）
   */
  ruleset_version: string;
}
/**
 * 一件台上器材实例。试剂瓶以 apparatus_id 指向瓶器材卡、contents 装瓶装溶液；倾角由玩家指针方位角操作产生。
 */
export interface ApparatusInstance {
  /**
   * 实例唯一 ID（如 beaker-3）
   */
  instance_id: string;
  /**
   * 器材卡 ID，指向 apparatus 事实源
   */
  apparatus_id: string;
  position_mm: Position;
  /**
   * 容器倾角（度，绕容器中心；玩家操作产生，液面世界水平由表现层反向抵消）
   */
  rotation_deg: number;
  /**
   * 容器内物质（倾倒追加，体积由操作产生）
   */
  contents: SubstanceContent[];
  /**
   * 若为试剂瓶，指向瓶中溶液的 compound_id（浓度取该卡 reagent_solution）
   */
  reagent_compound_id?: string;
}
/**
 * 台面坐标（mm，原点左上角）
 */
export interface Position {
  /**
   * 横坐标 mm
   */
  x: number;
  /**
   * 纵坐标 mm
   */
  y: number;
}
/**
 * 容器内一份物质：物质 ID + 浓度（试剂瓶标签初始条件）+ 体积（操作产生）
 */
export interface SubstanceContent {
  /**
   * 引用 content 真实物质 ID
   */
  compound_id: string;
  /**
   * 浓度 mol/L（来自试剂瓶标签或稀释归一，非硬编码）
   */
  concentration_mol_L: number;
  /**
   * 本次加入/当前体积 L（由倾倒操作产生）
   */
  volume_L: number;
}
/**
 * 台面物理边界（真实尺度 mm）；摆放与重叠判定用。渲染按比例换算 px。
 */
export interface BenchBounds {
  /**
   * 台面宽 mm
   */
  width_mm: number;
  /**
   * 台面高 mm（纵深投影）
   */
  height_mm: number;
}
