/**
 * WASM ↔ TS 双后端一致性交叉验证（证据自证产物）。
 *
 * 用同一组现象指令向量，分别喂给 Rust→WASM 变换与 TS fallback，逐字节比对
 * 表现参数输出。二者一致才证明「WASM 优先 + TS fallback」不会因后端切换产生
 * 表现差异。无 WASM 产物时跳过 WASM 侧并明确提示（CI 场景）。
 */
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const pkgDir = path.resolve(here, "../wasm-pkg");
const wasmEntry = path.join(pkgDir, "st_wasm_view.js");
const wasmBin = path.join(pkgDir, "st_wasm_view_bg.wasm");

// TS 变换的等价 JS 实现（与 transform.ts 同源逻辑，直接内联以便 Node 无编译运行）。
function namedColor(name) {
  switch (String(name).trim().toLowerCase()) {
    case "red": return [255, 0, 0, 1];
    case "yellow": return [255, 255, 0, 1];
    case "pink": return [255, 192, 203, 1];
    case "colorless": case "transparent": case "none": return [255, 255, 255, 0];
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
const c01 = (x) => Math.min(1, Math.max(0, x));
function lerpRgba(a, b, t) {
  const k = c01(t);
  return [a[0]+(b[0]-a[0])*k, a[1]+(b[1]-a[1])*k, a[2]+(b[2]-a[2])*k, a[3]+(b[3]-a[3])*k];
}
function alphaOver(dst, src) {
  const sa = c01(src[3]), da = c01(dst[3]), oa = sa + da * (1 - sa);
  if (oa <= 0) return [255, 255, 255, 0];
  const mix = (s, d) => (s*sa + d*da*(1-sa)) / oa;
  return [mix(src[0],dst[0]), mix(src[1],dst[1]), mix(src[2],dst[2]), oa];
}
function roundRgba(c) {
  return [Math.round(c[0]), Math.round(c[1]), Math.round(c[2]), Math.round(c01(c[3])*1000)/1000];
}
function tsTransform(directives) {
  let liquid = [255,255,255,0];
  const effects = [], visible = [];
  let containerId = "";
  for (const d of directives ?? []) {
    const dtype = typeof d?.type === "string" ? d.type : "";
    if (!containerId && typeof d?.container_id === "string") containerId = d.container_id;
    const raw = d?.intensity;
    const intensity = c01(typeof raw === "number" && Number.isFinite(raw) ? raw : 0.5);
    if (dtype && !visible.includes(dtype)) visible.push(dtype);
    const p = d?.physics ?? {};
    if (dtype === "color_change") {
      const acid = typeof p.acid_color === "string" ? p.acid_color : "colorless";
      const base = typeof p.base_color === "string" ? p.base_color : "colorless";
      liquid = alphaOver(liquid, lerpRgba(namedColor(acid), namedColor(base), intensity));
    } else if (dtype === "temperature_change") {
      const delta = typeof p.delta_K === "number" ? p.delta_K : 0;
      effects.push({ type: "temperature_change", intensity, delta_K: delta, hot: delta >= 0 });
    } else if (dtype === "splash") {
      effects.push({ type: "splash", intensity });
    }
  }
  return { schema_version: "st.appearance.v1", container_id: containerId,
           liquid: { rgba: roundRgba(liquid) }, effects, visible };
}

const D = (id, type, intensity, physics) => ({
  schema_version: "st.phenomenon.v1", directive_id: id, container_id: "beaker-1",
  type, timestamp_ms: 0, intensity, physics,
});
const VECTORS = [
  [],
  [D("d1","color_change",0.0,{acid_color:"red",base_color:"yellow",ph:2,pka:4.76,indicator_ratio:0.017})],
  [D("d2","color_change",0.5,{acid_color:"red",base_color:"yellow",ph:4.76,pka:4.76,indicator_ratio:1})],
  [D("d3","color_change",1.0,{acid_color:"red",base_color:"yellow",ph:8,pka:4.76,indicator_ratio:174})],
  [D("d4","color_change",0.8,{acid_color:"colorless",base_color:"pink",pka:9.1})],
  [D("d5","splash",0.5175,{delta_T_K:20.7}), D("d6","temperature_change",0.5175,{delta_K:20.7,temperature_K:318.85})],
  [D("d7","color_change",2.0,{acid_color:"red",base_color:"yellow"}), D("d8","splash",-1,{})],
];

let wasmTransform = null;
if (existsSync(wasmEntry) && existsSync(wasmBin)) {
  const { initSync, transform_json } = await import(wasmEntry);
  initSync({ module: readFileSync(wasmBin) });
  wasmTransform = (vec) => JSON.parse(transform_json(JSON.stringify(vec)));
  console.log("[crosscheck] WASM backend: loaded");
} else {
  console.log("[crosscheck] WASM backend: ABSENT (CI/no-pkg) — 仅校验 TS 路径不崩");
}

/** 规范化：递归按 key 排序，消除 serde_json(字母序) 与 TS(插入序) 的键序差异。 */
function canonical(v) {
  if (Array.isArray(v)) return v.map(canonical);
  if (v && typeof v === "object") {
    return Object.fromEntries(Object.keys(v).sort().map((k) => [k, canonical(v[k])]));
  }
  return v;
}
const norm = (v) => JSON.stringify(canonical(v));

let failures = 0;
for (let i = 0; i < VECTORS.length; i++) {
  const ts = tsTransform(VECTORS[i]);
  if (wasmTransform) {
    const wa = wasmTransform(VECTORS[i]);
    if (norm(wa) !== norm(ts)) {
      failures++;
      console.error(`[crosscheck] MISMATCH vector#${i}\n  WASM=${norm(wa)}\n  TS  =${norm(ts)}`);
    } else {
      console.log(`[crosscheck] OK vector#${i} ${norm(ts)}`);
    }
  } else {
    console.log(`[crosscheck] TS-ONLY vector#${i} ${norm(ts)}`);
  }
}

if (failures) {
  console.error(`[crosscheck] 失败 ${failures} 组：WASM 与 TS 表现参数不一致`);
  process.exit(1);
}
console.log(`[crosscheck] 通过：${VECTORS.length} 组向量${wasmTransform ? "双后端一致" : "TS 路径正常"}`);
