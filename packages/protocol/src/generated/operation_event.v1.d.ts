// GENERATED from schemas/operation_event.v1.schema.json — DO NOT EDIT. Run pnpm build:types.

/**
 * 操作原语：place/remove=器材取放；pour=倾倒转移；tilt=倾角调整；take_reagent=从试剂架取用
 */
export type OpType = "place" | "remove" | "pour" | "tilt" | "take_reagent";

/**
 * st.operation_event.v1 — 操作原语事件（008）：取放/倾倒/倾角等一切玩家操作。物理量按操作类型承载，一切数值由操作与求解产生、绝无预设配比。事件幂等由 event_id 保证，供台面状态重建与现象溯源。
 */
export interface OperationEvent {
  schema_version: "st.operation_event.v1";
  /**
   * 事件唯一 ID（内容寻址或递增序列，保证幂等）
   */
  event_id: string;
  op_type: OpType;
  /**
   * 事件时间戳 ms（相对台面会话）
   */
  timestamp_ms: number;
  /**
   * 操作源器材实例（取放/倾倒时必填）
   */
  source_instance_id?: string;
  /**
   * 操作目标器材实例（倾倒时必填）
   */
  target_instance_id?: string;
  payload?: OpPayload;
}
/**
 * 按操作类型承载的物理量；倾倒的 transferred_volume_L 由流速对时间积分产生，非预设。
 */
export interface OpPayload {
  /**
   * 取用/倾倒涉及的物质 ID
   */
  compound_id?: string;
  position_mm?: {
    x: number;
    y: number;
  };
  /**
   * 倾角（度）
   */
  rotation_deg?: number;
  /**
   * 倾倒触发时的容器倾角（度）
   */
  tilt_angle_deg?: number;
  /**
   * 本次倾倒转移体积 L（托里拆利积分结果，非预设）
   */
  transferred_volume_L?: number;
  /**
   * 倾倒时液面到瓶口的有效液柱高 mm（流速物理输入）
   */
  head_height_mm?: number;
  /**
   * 操作持续时间 ms
   */
  duration_ms?: number;
}
