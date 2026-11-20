// M0 WASM 现象内核帧预算验证（Node 22 原生 WebAssembly，无第三方依赖）
// 复用：WebAssembly 标准 API + 已编译的 st_phenomenon_kernel.wasm
import { readFileSync, writeFileSync } from 'node:fs';
import { performance } from 'node:perf_hooks';

const wasmPath = new URL('./target/wasm32-unknown-unknown/release/st_phenomenon_kernel.wasm', import.meta.url);
const bytes = readFileSync(wasmPath);
const { instance } = await WebAssembly.instantiate(bytes, {});
const { memory, init, step, count, positions_ptr, checksum } = instance.exports;

const FRAME_MS = 16.7; // 固定 60fps 帧预算（台账 SP-1 / ADR-0008）
const results = [];

function measure(nParticles, frames = 180) {
  const n = init(nParticles, 12345);
  // 预热 10 帧，排除 JIT 首次编译
  for (let f = 0; f < 10; f++) step(1 / 60);
  const samples = [];
  let activeLast = 0;
  for (let f = 0; f < frames; f++) {
    const t0 = performance.now();
    activeLast = step(1 / 60);
    samples.push(performance.now() - t0);
  }
  samples.sort((a, b) => a - b);
  const p = (q) => +samples[Math.min(samples.length - 1, Math.floor(q * samples.length))].toFixed(4);
  // 校验线性内存：读回第一个粒子的 x，确认 WASM 状态与 JS 可见内存一致
  const ptr = positions_ptr();
  const view = new Float32Array(memory.buffer, ptr, 4);
  const firstX = +view[0].toFixed(6);
  const cs = +checksum().toFixed(4);
  return {
    requested: nParticles, actual: n, frames,
    p50_ms: p(0.50), p95_ms: p(0.95), p99_ms: p(0.99), max_ms: +samples[samples.length - 1].toFixed(4),
    budget_ms: FRAME_MS,
    within_budget: p(0.95) < FRAME_MS,
    active_particles_last_frame: activeLast,
    first_particle_x: firstX,
    checksum: cs,
  };
}

// 多规模：500（既有 Pixi 基线）、1000、2000、4096（MAX）
for (const n of [500, 1000, 2000, 4096]) {
  results.push(measure(n));
}

// 确定性复验：同 seed 两次 init 前 60 帧的 checksum 必须一致
const s1 = (() => { init(500, 777); for (let f = 0; f < 60; f++) step(1/60); return +checksum().toFixed(6); })();
const s2 = (() => { init(500, 777); for (let f = 0; f < 60; f++) step(1/60); return +checksum().toFixed(6); })();
const out = {
  title: 'M0 WASM 现象内核帧预算验证',
  runtime: 'Node ' + process.version + ' WebAssembly (native)',
  wasm_bytes: bytes.length,
  wasm_imports: 0,
  cases: results,
  determinism: { seed: 777, frames: 60, checksums: [s1, s2], identical: s1 === s2 },
  summary: {
    all_within_budget: results.every(r => r.within_budget),
    max_p95_ms: Math.max(...results.map(r => r.p95_ms)),
    deterministic_same_seed: s1 === s2,
  },
  source: 'st_phenomenon_kernel.wasm 由 cargo build --target wasm32-unknown-unknown --release 编译；零外部 import',
};
writeFileSync(new URL('./wasm_bench_result.json', import.meta.url), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2));
