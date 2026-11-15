// ST Crucible · M0 容器内现象内核最小验证（可行性验证，非产品代码）
// 目的：证明 Rust -> wasm32-unknown-unknown 工具链可编译、可在浏览器/Node 实例化、
//       且固定 60fps 帧预算(16.7ms)内可完成 N 粒子的现象步进。
// 设计：纯计算、静态线性缓冲、C ABI 导出，零外部 import（不依赖 wasm-bindgen）。
//       粒子状态 = 容器内现象的"表现层"占位，化学事实由服务端求解器负责，二者解耦。

const MAX: usize = 4096;
const STRIDE: usize = 4; // x, y, vx, vy (f32)
const CELLS: usize = MAX * STRIDE;

static mut BUF: [f32; CELLS] = [0.0; CELLS];
static mut N: usize = 0;
static mut SEED: u32 = 0x9e37_79b9;

// xorshift32：可复现的确定性伪随机，不引入 rand crate（不重复造轮子 / 免下载）
fn rnd() -> f32 {
    unsafe {
        let mut x = SEED;
        x ^= x << 13;
        x ^= x >> 17;
        x ^= x << 5;
        SEED = x;
    }
    (unsafe { SEED } as f32) / (u32::MAX as f32)
}

/// 初始化 n 个粒子：位置散布于容器内 [0,1]²，速度随机。返回实际粒子数。
#[no_mangle]
pub extern "C" fn init(n: usize, seed: u32) -> usize {
    let count = if n > MAX { MAX } else { n };
    unsafe {
        SEED = if seed == 0 { 0x9e37_79b9 } else { seed };
        N = count;
        for i in 0..count {
            let b = i * STRIDE;
            BUF[b] = rnd();            // x
            BUF[b + 1] = rnd();        // y
            BUF[b + 2] = (rnd() - 0.5) * 0.02; // vx
            BUF[b + 3] = (rnd() - 0.5) * 0.02; // vy
        }
    }
    count
}

/// 现象步进：浮力 + 布朗扰动 + 容器壁反弹 + 轻微阻尼。dt 为秒。
/// 返回本帧"活跃"粒子数（用于验证循环确实执行而非被优化掉）。
#[no_mangle]
pub extern "C" fn step(dt: f32) -> usize {
    let mut active = 0usize;
    unsafe {
        let n = N;
        for i in 0..n {
            let b = i * STRIDE;
            let mut x = BUF[b];
            let mut y = BUF[b + 1];
            let mut vx = BUF[b + 2];
            let mut vy = BUF[b + 3];
            // 浮力向上 + 确定性布朗扰动
            vy -= 0.15 * dt;                 // 上浮（气泡/沉淀翻涌的占位）
            vx += (rnd() - 0.5) * 0.004 * dt;
            vy += (rnd() - 0.5) * 0.004 * dt;
            vx *= 0.995;                      // 阻尼
            vy *= 0.995;
            x += vx;
            y += vy;
            // 容器壁 [0,1]² 反弹
            if x < 0.0 { x = -x; vx = -vx; } else if x > 1.0 { x = 2.0 - x; vx = -vx; }
            if y < 0.0 { y = -y; vy = -vy; } else if y > 1.0 { y = 2.0 - y; vy = -vy; }
            BUF[b] = x; BUF[b + 1] = y; BUF[b + 2] = vx; BUF[b + 3] = vy;
            if x > 0.0 && x < 1.0 && y > 0.0 && y < 1.0 { active += 1; }
        }
    }
    active
}

#[no_mangle]
pub extern "C" fn count() -> usize { unsafe { N } }

#[no_mangle]
pub extern "C" fn positions_ptr() -> *const f32 {
    // 用 addr_of! 取裸地址，避免对 static mut 建立共享引用（static_mut_refs lint）
    core::ptr::addr_of!(BUF) as *const f32
}

/// 校验和：供测试端确认 WASM 线性内存与 JS 读取一致（防止"跑了但没生效"）。
#[no_mangle]
pub extern "C" fn checksum() -> f32 {
    let mut s = 0.0f32;
    unsafe {
        for i in 0..N * STRIDE { s += BUF[i]; }
    }
    s
}
