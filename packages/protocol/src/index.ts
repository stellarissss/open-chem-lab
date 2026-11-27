// @st/protocol 公共出口。协议版本常量是解耦双方的唯一握手凭据。
export const PHENOMENON_SCHEMA_VERSION = "st.phenomenon.v1" as const;
export const SAVE_SCHEMA_VERSION = "st.save.v1" as const;
export const TIMELINE_SCHEMA_VERSION = "st.timeline.v1" as const;
export const COMPOUND_SCHEMA_VERSION = "st.compound.v1" as const;
export const APPARATUS_SCHEMA_VERSION = "st.apparatus.v1" as const;
export const REACTION_RULE_SCHEMA_VERSION = "st.reaction_rule.v1" as const;
export const SOLUTION_SPECIATION_SCHEMA_VERSION = "st.solution_speciation.v1" as const;
export const REPORT_SCHEMA_VERSION = "st.report.v1" as const;

export type { PhenomenonDirective } from "./generated/phenomenon.v1.js";
export type { SaveGame, ApparatusPlacement, SubstanceRef } from "./generated/save.v1.js";
export type {
  SpeciationTimeline,
  Keyframe,
  SpeciationSnapshot,
  Curve,
} from "./generated/timeline.v1.js";
export type { Compound } from "./generated/compound.v1.js";
export type { Apparatus } from "./generated/apparatus.v1.js";
export type { ReactionRule } from "./generated/reaction_rule.v1.js";
export type { SolutionSpeciation } from "./generated/solution_speciation.v1.js";
export type {
  LabReport,
  Operation,
  Snapshot,
  SpeciesValue,
  Curve as ReportCurve,
  Reaction,
  SourceAnchor,
  Outcome,
  OutcomeSummary,
} from "./generated/report.v1.js";

// 现象类别：表现层注册表类型（内联联合，从指令字段提取）。
import type { PhenomenonDirective } from "./generated/phenomenon.v1.js";
export type PhenomenonType = PhenomenonDirective["type"];
