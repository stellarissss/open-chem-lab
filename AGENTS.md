# AGENTS.md · AI 第一站

> 编码 Agent 天然优先读根目录 `AGENTS.md`。本文件只放**现场指针 + 当前焦点 + 变更留痕**，是上下文压缩后的恢复锚点。
> 保持极简——项目定义、技术、流程的正文一律不放在这里。

## 必读顺序（每次开工）

1. 本文件（当前焦点 + 留痕）
2. `docs/02-Roadmap.md` —— 当前进度、里程碑、薄切片清单、下一步
3. `docs/01-Architecture.md` —— 唯一技术与产品真理源（按需读相关节）
4. `docs/03-DocDD-Process.md` —— 开发流程与 spec 写法
5. `docs/specs/` —— 当前切片的详细规格

> `docs/归档/` 是历史文档（决策过程、旧规划、调研证据、ADR/design 原文），**开发时不读**，防止上下文污染。

## 一句话项目卡

**ST Crucible / 《ST实验室》**：专业、好玩、开源可自托管的仿真化学实验室；实验台唯一主视图 + 出版级写实 2D + 容器内 WASM 现象 + 服务端动态定量求解；数值零错红线内好玩优先；单人 + AI Agent、敏捷 + 文档驱动、不设时间预算。详见 `docs/01-Architecture.md`。

## 硬约束（违反前必读 `docs/01-Architecture.md` 第七节）

1. **事实零错**是红线，近似不进化学事实层；红线内好玩优先。
2. **不重复造轮子**：动手前先搜开源成品与官方文档。
3. **许可证**：主代码 LGPL-3.0；AGPL/GPLv2-only 严格隔离；CC-BY-SA 数据独立仓；LPPL 只取编译输出物。
4. **重大变更**（产品定义/技术栈/许可证基线/验收口径）先与用户确认并同步真理源；L0 纠错直接改+留痕。

## 当前焦点

- 阶段三 M1 迭代中：切片 001「骨架搭建」✅ 已完成并实测通过（2026-11-20）。下一步：切片 002「内容 schema」——粗稿已就位 `specs/spec-002-内容schema与中和体系.md`，开工时就地补全为正式规格再执行（链式闭环见 `03-DocDD-Process.md` 2.3）。
- 产品骨架：pnpm monorepo（`@st/protocol` / `@st/gateway` / `@st/web-ui` / `solver-worker` / `reaktoro-service` 占位）+ Docker Compose 单机自托管。构建 `pnpm build`；起服 `docker compose -f deploy/docker-compose.minimal.yml up -d --build`；许可证门禁 `python3 tests/license-scan/scan.py`。

## 变更留痕（最近在上）

- 2026-11-20：开发流程补上「链式闭环」——`03-DocDD-Process.md` 新增 2.3「回写即铺路」双轨机制（回写时预写下一 spec 粗稿 + 路线图指向），spec 两阶段就地演进（粗稿→正式）；据新流程写好 `spec-002-内容schema与中和体系` 粗稿（聚焦酸碱中和样例，具体物质/数值待开工确认）。
- 2026-11-20：M1 切片 001「骨架搭建」完成——pnpm monorepo + protocol schema/类型生成 + Fastify gateway(health/WS) + React/Vite 壳页 + Python worker + reaktoro 占位 + Compose 四服务 + CI 雏形；全量构建/联调/license-scan 实测通过；Windows 实机待用户补测。
- 2026-11-20：文档体系重构完成——台账/CHARTER/旧规划/ADR/design/research/CHANGELOG 归档；新建 `01-Architecture`（唯一真理源）/`02-Roadmap`/`03-DocDD` + `specs/spec-001`；AGENTS/README/CONTRIBUTING/CREDITS/模板/CI 全量对齐；现行文档零断链。
