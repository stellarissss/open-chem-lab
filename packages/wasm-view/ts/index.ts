/**
 * @st/wasm-view 公共入口：现象指令 → 表现参数。
 *
 * 优先使用 Rust→WASM 变换（生产构建，pkg/ 存在时）；WASM 不可用时使用逐行等价的
 * TS fallback（CI 无 WASM 产物）。两条路径对外接口一致，行为由交叉测试保证一致。
 * 渲染层只需 await initView() 一次，之后同步调用 transformDirectives()。
 */
import type { PhenomenonDirective } from "@st/protocol";
import { transform as tsTransform, type Appearance } from "./transform.js";

export type { Appearance } from "./transform.js";
export { namedColor, lerpRgba, alphaOver } from "./transform.js";

import wasmInit, { transform_json as wasmTransformJson } from "../wasm-pkg/st_wasm_view.js";

/** 静态 import 胶水：Vite 在 dev 预构建、build 打包时都会正确处理 new URL(...wasm)。 */
type WasmModule = {
  transform_json: (json: string) => string;
};

let wasm: WasmModule | null = null;
/** 缓存初始化 Promise：StrictMode 双挂载时两次调用 await 同一结果，避免竞态。 */
let initPromise: Promise<{ backend: "wasm" | "ts" }> | null = null;

/**
 * 初始化变换器。尝试加载 WASM；任何失败（无产物/环境不支持）静默降级到 TS。
 * 幂等：多次调用只尝试一次。
 */
export async function initView(): Promise<{ backend: "wasm" | "ts" }> {
  if (initPromise) return initPromise;
  initPromise = (async () => {
    try {
      await wasmInit();
      wasm = { transform_json: wasmTransformJson };
      return { backend: "wasm" as const };
    } catch (err) {
      /* WASM 不可用（无 WebAssembly/环境不支持）：降级到 TS 等价实现 */
      console.warn("[wasm-view] WASM 初始化失败，降级 TS:", err);
      return { backend: "ts" as const };
    }
  })();
  return initPromise;
}

/** 同步变换：指令数组 → 表现参数。必须先 await initView()（未初始化时按 TS 处理）。 */
export function transformDirectives(directives: PhenomenonDirective[]): Appearance {
  if (wasm) {
    try {
      return JSON.parse(wasm.transform_json(JSON.stringify(directives))) as Appearance;
    } catch {
      /* WASM 变换异常不应击穿渲染层，降级到 TS */
    }
  }
  return tsTransform(directives);
}

/** 当前实际后端，供诊断面板显示。 */
export function viewBackend(): "wasm" | "ts" {
  return wasm ? "wasm" : "ts";
}
