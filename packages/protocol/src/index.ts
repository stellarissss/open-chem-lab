// @st/protocol 公共出口。协议版本常量是解耦双方的唯一握手凭据。
export const PHENOMENON_SCHEMA_VERSION = "st.phenomenon.v1" as const;
export const SAVE_SCHEMA_VERSION = "st.save.v1" as const;
export const TIMELINE_SCHEMA_VERSION = "st.timeline.v1" as const;

export type { PhenomenonDirective } from "./generated/phenomenon.v1.js";
export type { SaveGame, ApparatusPlacement, SubstanceRef } from "./generated/save.v1.js";
export type {
  SpeciationTimeline,
  Keyframe,
  SpeciationSnapshot,
  Curve,
} from "./generated/timeline.v1.js";

// 现象类别：表现层注册表类型（内联联合，从指令字段提取）。
import type { PhenomenonDirective } from "./generated/phenomenon.v1.js";
export type PhenomenonType = PhenomenonDirective["type"];
