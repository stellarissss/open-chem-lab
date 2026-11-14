# ADR-0003 · Web 优先 + WASM 热路径 + 后端重计算

- **状态**：已接受（需求方 2026-11-13 四项决策之一，`CHARTER` D2）
- **关联**：`CHARTER` D2、`design/01`、`design/05`、`research/02`

## 背景

需求是「部署在自己的服务器上」「性能最佳」「2D/3D 均可」。备选形态：纯 Web / Web + 桌面双端 / 先桌面再 Web 化。

调研事实：
- `Sandspiel`（MIT，★3,226）已是 **Rust→WASM + WebGL + Web Worker** 的落沙引擎，构建链现成（`wasm-pack build`）。
- `@rdkit/rdkit` MinimalLib 是**零依赖 WASM**，可在浏览器跑 SMILES/子结构/SMARTS。
- The Powder Toy 是 C++/SDL 桌面，GPL-3.0；Godot（MIT，★120k）虽可出 Web，但要维护两套渲染。
- 用户明确「部署在自己的服务器上」，且上一轮已选 Web 端（允许后端重计算）。

## 备选

| 方案 | 优点 | 缺点 |
|---|---|---|
| **纯 Web（Docker Compose）** | 浏览器直接玩、手机/平板可开、一键自托管、一套代码 | 3D 性能受浏览器限制（可控） |
| Web + 桌面双端 | 3D 与性能更强 | 两套渲染与构建，维护成本翻倍 |
| 先桌面再 Web 化 | 起步快 | 后期移植成本高，与「自托管服务器」目标冲突 |

## 决策

**纯 Web 优先 + 允许后端重计算**：
- 客户端：React + TS + Vite；PixiJS/WebGL2 渲染 2D 粒子；R3F/Three.js 做 3D 器材；3Dmol.js 做分子视图。
- 仿真核心：Rust→WASM，跑在 **Web Worker + OffscreenCanvas**，热路径 60fps、零网络往返。
- 服务端：gateway（REST/WS）+ chem-worker（RDKit/Cantera 冷路径）+ PG/Cartridge + Redis + 本地卷/MinIO。
- 部署：Docker Compose，**单机 4C8G 可跑**（最小 4 容器）。
- 离线：Service Worker + IndexedDB 缓存前端与规则包，**断网也能玩**。

## 理由

1. **复用最大化**：Sandspiel 的 WASM 链路、RDKit.js、3Dmol.js、R3F 全是 Web 原生，选 Web 几乎零移植成本（「不重复造轮子」）。
2. **性能最佳**：热路径全在客户端 WASM（0 RTT），温路径 Redis < 20ms，冷路径异步不阻塞渲染 —— 比「所有计算都在服务端」更快。
3. **自托管友好**：无客户端安装、无账号云依赖、数据留在自己服务器。
4. **2D/3D 均可**：两种渲染共享同一仿真状态（`design/02`），不像桌面双端要同步两套状态。
5. **全局总成本最低**：一套代码、一套构建、一套部署。

## 影响

- `design/01` 三级路径与部署拓扑基于此决策。
- `design/05` 技术栈锁定 TS/Rust/Python 三语言 + pnpm monorepo。
- 移动端用响应式 PWA，**不做原生 App**（纯 Web 的自然结果）。
- 3D 性能预算：R3F 场景仅器材与分子，粒子沙盒仍是 WebGL2 2D 网格，避免双重开销。

## 待 M0 验证

1. `wasm-pack build` 在当前工具链可跑通；改 `species.rs` 加元素是否顺利。
2. WASM 网格 512² 在中端设备能否稳定 60fps（不达标则降到 256² 或脏矩形更新）。
3. RDKit.js WASM 体积与首次加载耗时（只按需懒加载，不进主 bundle）。
4. gateway 语言在 Fastify(Node) 与 axum(Rust) 间实测二选一。

## 反面约束

不得为了 3D 效果把粒子仿真搬进 Three.js 场景导致 60fps 失守；不得引入需要安装的桌面客户端作为主交付形态。
