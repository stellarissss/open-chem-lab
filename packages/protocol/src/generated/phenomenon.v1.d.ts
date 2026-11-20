// GENERATED from schemas/phenomenon.v1.schema.json — DO NOT EDIT. Run pnpm build:types.

/**
 * st.phenomenon.v1 — 求解层与表现层的解耦协议。服务端只发『现象指令』，WASM 表现层只认指令 ID 与物理量，不认分子、不认求解细节。数值零错红线不作用于本协议（表现层可夸张）。
 */
export interface PhenomenonDirective {
  /**
   * 协议版本常量，解耦双方的唯一握手凭据
   */
  schema_version: "st.phenomenon.v1";
  /**
   * 指令唯一 ID，供幂等与回放去重
   */
  directive_id: string;
  /**
   * 目标容器/器材 ID
   */
  container_id: string;
  /**
   * 现象类别（表现层注册表，新增类别走协议版本升级，不进化学事实层）
   */
  type:
    | "liquid_change"
    | "gas_bubble"
    | "precipitate"
    | "flame"
    | "splash"
    | "color_change"
    | "temperature_change"
    | "crystallization"
    | "smoke"
    | "glow"
    | "phase_separation"
    | "motion";
  /**
   * 相对仿真起点的毫秒时间戳，驱动时间轴对齐
   */
  timestamp_ms: number;
  /**
   * 归一化表现强度（可夸张，非化学量）
   */
  intensity?: number;
  /**
   * 表现持续时长；0 表示瞬时事件
   */
  duration_ms?: number;
  /**
   * 关联物理量快照（仅表现所需，如温度/体积，均为显示值）
   */
  physics?: {
    [k: string]: unknown;
  };
}
