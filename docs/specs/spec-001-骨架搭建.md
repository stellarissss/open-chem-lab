# spec-001 · 骨架搭建

## 目标

建立可运行的最小工程骨架：前后端常驻本地服务器 + Docker Compose 单机自托管，让后续切片有一个可增量集成、可验证的底座。**验证架构而非堆功能**——本切片不需要任何真实化学体系或求解逻辑。

## 范围

**做**：
- pnpm monorepo 骨架（`schemas/` `content/` `packages/` `deploy/` 目录与空占位）。
- `protocol` 包：定义 `st.phenomenon.v1` / 存档 / 时间轴的最小类型与 JSON Schema（契约先行）。
- `gateway`（Fastify, Node/TS）：`GET /api/v1/health` 健康检查 + WS 握手骨架。
- `web` 前端（React + Vite）：空实验台壳页面，能显示后端 health 状态。
- `solver-worker`（Python 3.11 + lockfile）：空 worker 进程骨架（不接求解逻辑）。
- `reaktoro-service`：独立的 conda 镜像占位（LGPL-2.1 动态链接的可替换性契约先落 `NOTICE`/`lgpl-link-check`，本切片不接真实求解）。
- `postgres` + 本地卷：最小 Compose 编排。
- CI 门禁雏形：`docs-and-compliance` / `license-scan` 接入（产品级 `golden-cases`/`schema-validate` 随后续切片加）。

**不做**（明确边界）：
- 任何真实反应数据或求解逻辑（→ spec-002/003）。
- 物种面板、时间轴、WASM 现象、实验报告（→ spec-004/005/006）。
- 程序化 3D 器材、教学功能、断网可玩（永久不做或长线）。
- 多机 / 公共 Demo（锁定单机自托管）。

## 验收标准

1. `docker compose -f deploy/docker-compose.minimal.yml up -d` 后，`web + gateway + solver-worker + postgres` 服务健康，浏览器打开能看到前端壳页并显示后端 health=OK。
2. `GET /api/v1/health` 返回 200；WS 可建立连接。
3. `protocol` 包的核心 schema 可被各语言侧引用（TS 类型生成成功）。
4. **双平台**：Linux 实跑一次通过；Windows（WSL2/Docker Desktop）按 `deploy/README-windows.md` 逐项静态核查通过（实机若受限须标注）。
5. 全仓无 CRLF、路径小写 snake_case、无明文凭证入库。
6. `license-scan` / `docs-and-compliance` 门禁通过；无 AGPL / GPLv2-only 依赖。
7. 完成后如实记录做了哪些验证、哪些受限（不设强制门禁，见 `03-DocDD-Process.md` 第四节）。

## 技术要点

遵循 `01-Architecture.md`：
- 工程结构与依赖规则（第六节）：`protocol` 最底层不依赖任何包；`web-ui` 经 `gateway` 访问、不直连求解库；全仓路径小写 snake_case、`.gitattributes` 强制 LF。
- 技术栈锁定（第四节）：TypeScript 5.x / Rust / Python 3.11 + lockfile；网关 Fastify；PostgreSQL；前端 React + Vite + Zustand。
- 部署（第六节）：单机自托管、前后端常驻；reaktoro-service 经本机 UDS/回环通讯；运行期无需外网但本地服务器在线（不提供断网可玩）。
- 红线（第七节）：LGPL-3.0 三文件 + `NOTICE` 显著声明；Reaktoro LGPL-2.1 §6 义务（动态链接、运行时可替换）；AGPL/GPLv2-only 隔离；CC-BY-SA 数据独立仓 submodule。

**复用优先**：Compose / Fastify / Vite / pnpm 全部用成熟模板与官方文档，不自造脚手架；动手前先核对官方文档与许可证。

## 任务拆解

1. 建 monorepo 骨架与 workspace 配置（`package.json` / `pnpm-workspace.yaml` / lockfile）。
2. 落 `protocol` 最小 schema 与类型生成。
3. 起 `gateway`（health + WS 握手）与 `web` 壳页。
4. 起 `solver-worker` 空进程骨架、`reaktoro-service` 镜像占位。
5. 写 `deploy/docker-compose.minimal.yml` + `.env.example`，双平台跑通。
6. 接 CI 雏形门禁，跑验收标准逐项核对。

## 状态

已完成。
