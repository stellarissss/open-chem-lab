/**
 * st.phenomenon.v1 指令 → st.appearance.v1 表现参数（纯函数变换）。
 *
 * 与 Rust 源（src/lib.rs）逐行等价的 TS fallback：当运行环境无 WASM 产物时使用
 * （CI 的 pkg/ 与 *.wasm 不入库）。二者由同一组向量交叉验证，保证行为一致。
 * 只认指令字段与表现量，不认分子、不认求解细节、不复算化学量。
 */

import type { PhenomenonDirective } from "@st/protocol";

export interface Appearance {
  schema_version: "st.appearance.v1";
  container_id: string;
  liquid: { rgba: [number, number, number, number] };
  effects: Array<{ type: string; intensity: number; delta_K?: number; hot?: boolean }>;
  visible: string[];
}

type RGBA = [number, number, number, number];

/** 命名色 → RGBA；无色为 alpha=0 透明白。未知色诚实降级为透明。 */
export function namedColor(name: string): RGBA {
  switch (name.trim().toLowerCase()) {
    case "red": return [255, 0, 0, 1];
    case "yellow": return [255, 255, 0, 1];
    case "pink": return [255, 192, 203, 1];
    case "colorless":
    case "transparent":
    case "none": return [255, 255, 255, 0];
    case "orange": return [255, 165, 0, 1];
    case "blue": return [0, 0, 255, 1];
    case "green": return [0, 128, 0, 1];
    case "purple": return [128, 0, 128, 1];
    case "brown": return [165, 42, 42, 1];
    case "white": return [255, 255, 255, 1];
    case "black": return [0, 0, 0, 1];
    default: return [255, 255, 255, 0];
  }
}

const clamp01 = (x: number): number => Math.min(1, Math.max(0, x));

/** acid ↔ base 线性插值，t=intensity(fraction_base)。 */
export function lerpRgba(acid: RGBA, base: RGBA, t: number): RGBA {
  const k = clamp01(t);
  return [
    acid[0] + (base[0] - acid[0]) * k,
    acid[1] + (base[1] - acid[1]) * k,
    acid[2] + (base[2] - acid[2]) * k,
    acid[3] + (base[3] - acid[3]) * k,
  ];
}

/** source-over alpha 合成。 */
export function alphaOver(dst: RGBA, src: RGBA): RGBA {
  const sa = clamp01(src[3]);
  const da = clamp01(dst[3]);
  const oa = sa + da * (1 - sa);
  if (oa <= 0) return [255, 255, 255, 0];
  const mix = (s: number, d: number) => (s * sa + d * da * (1 - sa)) / oa;
  return [mix(src[0], dst[0]), mix(src[1], dst[1]), mix(src[2], dst[2]), oa];
}

const roundRgba = (c: RGBA): [number, number, number, number] => [
  Math.round(c[0]), Math.round(c[1]), Math.round(c[2]),
  Math.round(clamp01(c[3]) * 1000) / 1000,
];

/** 纯变换入口：指令数组 → 表现参数。非法指令跳过，不抛。 */
export function transform(directives: PhenomenonDirective[]): Appearance {
  let liquid: RGBA = [255, 255, 255, 0];
  const effects: Appearance["effects"] = [];
  const visible: string[] = [];
  let containerId = "";

  for (const d of directives ?? []) {
    const dtype = typeof d?.type === "string" ? d.type : "";
    if (!containerId && typeof d?.container_id === "string") containerId = d.container_id;
    const rawI = d?.intensity;
    const intensity = clamp01(typeof rawI === "number" && Number.isFinite(rawI) ? rawI : 0.5);
    if (dtype && !visible.includes(dtype)) visible.push(dtype);

    const physics = (d?.physics ?? {}) as Record<string, unknown>;
    switch (dtype) {
      case "color_change": {
        const acid = typeof physics.acid_color === "string" ? physics.acid_color : "colorless";
        const base = typeof physics.base_color === "string" ? physics.base_color : "colorless";
        liquid = alphaOver(liquid, lerpRgba(namedColor(acid), namedColor(base), intensity));
        break;
      }
      case "temperature_change": {
        const delta = typeof physics.delta_K === "number" ? physics.delta_K : 0;
        effects.push({ type: "temperature_change", intensity, delta_K: delta, hot: delta >= 0 });
        break;
      }
      case "splash":
        effects.push({ type: "splash", intensity });
        break;
      default:
        break;
    }
  }

  return {
    schema_version: "st.appearance.v1",
    container_id: containerId,
    liquid: { rgba: roundRgba(liquid) },
    effects,
    visible,
  };
}
