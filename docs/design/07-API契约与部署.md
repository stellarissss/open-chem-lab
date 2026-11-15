# 07 · API 契约、部署、性能预算与许可证合规矩阵

> 依据：[决策台账](../11-问题与决策台账.md) 3.1 / 4.2 / 9.1 / 9.4 / 10.4 / A1 / 6.2；关联 ADR-0003、0005、0008。
> **v2.0**：删除二进制规则包下发、Yjs 协作、离线 / 断网语义、工坊导入、M3 教学端点；新增服务端求解、物种快照、时间轴、关注度上报；合规矩阵按 LGPL-3.0 重写；性能预算按 SP-1 帧预算重写。

## 一、API 契约（gateway）

风格：REST（资源 / 查询 / 管理）+ WebSocket（实时现象、物种快照、关注度）+ 内部任务队列（求解任务）。全部返回 `protocol` 包定义的类型，`schema` 版本随响应头 `X-ST-Schema-Version` 返回。**服务端为唯一事实源**，客户端不接受越权写入。

### 1.1 REST

| 方法 | 路径 | 用途 | 阶段 |
|---|---|---|---|
| `GET` | `/api/v1/health` | 健康检查 | M0 |
| `GET` | `/api/v1/compounds?q=&page=` | **可玩物质卡**检索（名称 / 分子式 / 知识点） | M1 |
| `GET` | `/api/v1/compounds/:id` | 可玩物质卡详情（含结构 SVG、物性、GHS、source） | M1 |
| `GET` | `/api/v1/apparatus` | 实验台器材清单与参数 | M1 |
| `GET` | `/api/v1/rules/:id` | 反应详情（含 `source` / `confidence` / `applicability` / 定量参数） | M1 |
| `POST` | `/api/v1/solve` | **服务端动态定量求解**：`(体系, 条件)` → 物种分布 + 现象指令 | M1 |
| `GET` | `/api/v1/speciation/:container_id` | 当前容器物种分布（分子 / 离子 / 络合 / 沉淀 / 浓度 / 活度 / pH） | M1 |
| `GET` | `/api/v1/timeline/:session_id` | 关键快照时间轴回放数据 | M1 |
| `POST` | `/api/v1/saves` | 保存轻量存档 | M1 |
| `GET` | `/api/v1/saves/:id` | 读取存档 | M1 |
| `POST` | `/api/v1/reports` | 生成**最小实验报告**（操作序列 / 曲线 / 反应式 / 来源） | M1 |
| `POST` | `/api/v1/uncovered` | 上报未命中体系（补体系日志，**不做 ML 预测**） | M2 |
| `GET` | `/api/v1/uncovered/stats` | 未覆盖统计（按频次排队补体系） | M2 |
| `GET` | `/api/v1/experiments` | 教材实验模板检索 | **长线**（不进 M1–M3） |
| `POST` | `/api/v1/assessments` | 操作测评 / xAPI 语句 | **长线** |
| `POST` | `/api/v1/lti/launch` | LTI 1.3 启动（ltijs） | **长线** |

> **已删除端点**：`GET /api/v1/rulesets/:version`（本地二进制规则包下载）、`POST /api/v1/rulesets/import`（规则包工坊）、`GET /api/v1/saves/:id/replay`（改由 `/timeline` 承载）、`POST /api/v1/compounds/search/structure`（不再以结构检索为规模主线）。

### 1.2 WebSocket

| 事件 | 方向 | 载荷 |
|---|---|---|
| `operation.report` | C→S | `{ session_id, container_id, action, ref, amount, conditions }` 实验台操作事件 |
| `solve.request` | C→S | `{ request_id, system, conditions }` 请求定量求解 |
| `solve.pending` | S→C | 求解入队提示（**表现层继续 60fps 动画，不阻塞**） |
| `solve.result` | S→C | `st.phenomenon.v1` 现象指令 + `speciation_ref` |
| `speciation.push` | S→C | 物种分布快照 + 时间戳（异步喂入，插值平滑） |
| `phenomenon.push` | S→C | 现象编排指令 |
| `attention.update` | C→S | **关注度上报**（视野内 / 刚被操作 / 时间轴聚焦）→ SP-1 算力配额依据 |

> **契约要点**：`solve.result` 是 `st.phenomenon.v1` 结构；求解耗时与帧率彻底解耦（ADR-0008 第 3 层）。**已删除** `collab.update`（Yjs CRDT）与 `presence`（多人在线状态）—— 台账 9.4 单人 + AI 体制、废弃复杂协作。

### 1.3 求解缓存键

```
key = sha256( canonical(system) + "|" + canonical(conditions) + "|" + ruleset_version )
```

Redis LRU；稳态冻结后复用（SP-1 第 4 层）；事件（加料 / 加热 / 改参数 / pH 突变）立即唤醒重算。

## 二、部署（Docker Compose · 前后端常驻）

### 2.1 服务清单

| 服务 | 端口 | 说明 | 最小部署 |
|---|---|---|---|
| `web` | 80 | Nginx 静态前端 + 写实 2D 资产 | 必需 |
| `gateway` | 3000 | REST + WS + 鉴权 | 必需 |
| `solver-worker` | 内部 | Python 3.11 + **phreeqpython 主引擎** / SciPy LSODA·BDF / Cantera / chempy 对拍（独立 worker，资源隔离） | 必需 |
| `reaktoro-service` | 内部 UDS | conda 镜像 + Reaktoro（LGPL-2.1 动态链接）；多相 / 固相 / 气相、高温高压、燃烧爆炸平衡终态与复杂体系，按需路由（D2 / D2-补） | 按需启用 |
| `postgres` | 5432 | 主库（参数 / 存档 / 时间轴） | 必需 |
| `redis` | 6379 | 缓存 / 会话 | 必需（单机可内嵌） |
| `minio` | 9000 | 存档 / 快照 / 资产 | 单机用本地卷 |
| `caddy` | 443 | 反代 + 自动 HTTPS | 可选 |

> **D6 已锁定「单机自托管」**（台账 §9.1）：上述服务全部运行在单台本地服务器的一个 Compose 项目内，`reaktoro-service` 经本机 UDS / 回环通讯，不引入多机。多机横向扩展与公共 Demo 后置长线。本章保证「前后端常驻本地服务器 + Win + Linux 双平台兼容」。

### 2.2 自托管步骤（M1 交付，双平台各给一套）

```bash
# Linux / macOS
git clone https://github.com/stellarissss/open-chem-lab.git
cd open-chem-lab
cp deploy/.env.example .env          # 设置 POSTGRES_PASSWORD / JWT_SECRET / 端口 / 域名
docker compose -f deploy/docker-compose.minimal.yml up -d
# 浏览器打开 http://<你的服务器>；前后端常驻，无需任何外部账号或云服务
```

```powershell
# Windows（WSL2 / Docker Desktop）—— 详见 deploy/README-windows.md
git clone https://github.com/stellarissss/open-chem-lab.git
cd open-chem-lab
copy deploy\.env.example .env
docker compose -f deploy/docker-compose.minimal.yml up -d
```

> **不提供「断网可玩」**：前后端缺一不可，废弃离线规则包 / Service Worker / IndexedDB（台账 4.2）。运行期可无外网，但本地服务器必须在线。

### 2.3 Win + Linux 双平台兼容（硬约束 C28，前置设计）

| 坑 | 对策 | 验证 |
|---|---|---|
| CRLF / LF | `.gitattributes` 强制 `* text=auto eol=lf`；`.sh` / `.yml` / `.env` 一律 LF | CI 检查无 CRLF |
| 路径大小写 | 全仓路径统一**小写 + snake_case**；禁止仅靠大小写区分文件 | CI 静态检查 |
| 卷挂载 | Docker Desktop / WSL2 与 Linux 语法差异；文档给两套命令，卷路径可配 | M0 双平台各跑一次 |
| 文件权限 | 容器以非 root 运行；不依赖宿主 umask | M0 验证 |
| 端口占用 | `.env` 可配置所有端口；检查 Windows 常见占用 | M0 验证 |
| TeX 转换管线 | 全程在 Docker 内执行，不依赖宿主 TeX 发行版 | M0 验证 |
| 求解库二进制 | `reaktoro-service` 使用 conda-forge 镜像（Reaktoro 仅 conda 分发）；LGPL-2.1 动态链接库在镜像内可替换 | M1 补验 |

### 2.4 环境要求

| 项 | 最低 | 推荐 |
|---|---|---|
| CPU / 内存 | 4C / 8G | 8C / 16G（求解器为 CPU 密集） |
| 磁盘 | 20 GB | 80 GB（含资产与快照） |
| 系统 | **Windows 10/11 + WSL2 或 Docker Desktop** / **Linux + Docker 24+ / Compose v2** | — |
| 网络 | 部署期需拉镜像与依赖；运行期无需外网，但**本地服务器必须在线** | — |

### 2.5 数据与备份

- PG 每日 `pg_dump`；本地卷 / MinIO 快照；参数库按 `rule_revision` 可回滚。
- 无状态服务可随时重建；`ruleset_version` 保证存档可解释。
- 升级流程：备份 → 拉新镜像 → DB migration（向前兼容）→ 灰度下发新参数库 → 回滚预案。

### 2.6 安全（自托管）

| 项 | 措施 |
|---|---|
| 认证 | 本地账号（argon2）+ 可选 OIDC；JWT 短期 + refresh |
| 传输 | Caddy 自动 HTTPS；WS 走 `wss` |
| 输入校验 | 所有 API 用 schema 校验；求解参数在**隔离 worker** 内解析，限制 CPU / 内存 / 超时 |
| **求解器资源隔离** | 刚性 ODE 可能不收敛 → worker 级 CPU / 内存 / 单步超时上限；SP-1 按帧预算动态配额 |
| 内容安全 | 参数与存档是数据，不执行任意代码；`confidence` 闸门 + AI 对拍 + 人工签核 |
| 依赖 | CI 许可证扫描 + `lgpl-link-check` + 依赖漏洞扫描 + 锁定版本 |
| 隐私 | 数据留在自托管实例；不上报第三方 |

## 三、许可证合规矩阵（**红线，CI 强制**）

### 3.1 主项目

| 项 | 值 |
|---|---|
| 主代码许可证 | **LGPL-3.0**（台账 A1 / ADR-0001） |
| 许可证交付 | `LICENSE`（总说明）+ `LICENSE.GPL-3`（GPLv3 全文）+ `LICENSE.LGPL-3`（LGPLv3 全文）+ `NOTICE`（显著声明） |
| 关键事实 | **LGPL-3.0 = GPLv3 全文 + 附加权限**，不是独立许可证；§4 要求同时随附两份全文（【补正 B】B1/B2） |
| 第三方组件 | 各自许可证保留，见 `CREDITS.md` / `NOTICE` / `assets/attribution/` |
| 内容数据 | 自有参数 LGPL-3.0；ORD 衍生规则 CC-BY-SA-4.0 独立仓 |

### 3.2 允许进入主构建产物的许可证（白名单）

`MIT` · `BSD-2-Clause` · `BSD-3-Clause` · `Apache-2.0` · `ISC` · `CC0-1.0` · `CC-BY-4.0`（需署名）· `CC-BY-3.0`（需署名）· **`LGPL-2.1`** · **`LGPL-3.0`** · `PostgreSQL` · `Python-2.0`

> FSF 兼容性（【补正 B】B4/B5）：LGPLv3 ↔ GPLv3 兼容；LGPLv2.1 ↔ GPLv2/v3 兼容；Apache-2.0 ↔ GPLv3 兼容；MIT / BSD / ISC 均为 GPL 兼容宽松许可。

### 3.3 禁止 / 限制

| 对象 | 许可 | 允许的方式 | 禁止的方式 |
|---|---|---|---|
| **tptmp** | **AGPL-3.0** | 只读参考 | **任何形态合并**：AGPLv3 与 GPLv3 严格意义不兼容（B6），网络使用即视为分发 |
| GPLv2-only 组件 | GPL-2.0-only | 只读参考 | 链接 / 合并 |
| The Powder Toy | GPL-3.0 | 只读设计参考 | **依台账 6.2 选型决策不纳入主链**（换证后许可证层面可行，但不重评）；拟引入须先提 ADR |
| PhET sims | GPL | 独立页面原样自托管 | 定制后并入主代码库 |
| H5P core | GPL-3.0 | 只读参考 / 独立进程 | 并入主构建产物 |
| cdk / Jmol-SwingJS | LGPL-2.1 | 只读参考 | 未纳入选型 |
| **Sandspiel** | MIT | 历史源码实读（数据驱动结论） | 落沙基座已退场，不进入产品链路 |

> **「为何换证却不引入 GPL 组件」**：换证是许可证立场（弱 copyleft、衍生回馈、解锁生态可能性），不纳入是选型决策（6.1 已废弃落沙基座，无真实缺口；引入会带来 §4/§6 义务与构建边界治理成本）。两者不矛盾，详见 ADR-0001。

### 3.4 特殊资产与数据的处理义务

| 对象 | 许可证 | 义务 | 落地 |
|---|---|---|---|
| **reaktoro-service（Reaktoro）** | **LGPL-2.1** | **独立微服务 + 动态链接 + 运行时可替换 + 显著声明 + 附 LGPL 全文 + 允许逆向调试 + 修改版源码可得**（§6 / §4） | conda 镜像内不静态编入二进制；经 UDS/protobuf 与主进程通讯；`NOTICE` 第 2 节；CI `lgpl-link-check` 校验服务镜像；**进程隔离不免除义务**（D2） |
| **tikz-chemlab 宏包源码** | LPPL-1.3c | 不改源码、不随产品分发；只转译**编译输出物**（Clause 1）；若改源码须按 Clause 6 改名 + 变更日志 + 附原件 | 构建期从 CTAN 拉取，源码不入库；`ASSETS.csv` 署名五作者 |
| **ord-data** | CC-BY-SA-4.0（数据）/ Apache-2.0（脚本） | 署名 + **相同方式共享** | **`data-ord/` 独立公开仓物理分离**，主仓仅 submodule；衍生规则标溯源；只抽事实性反应式 |
| **LabIcons** | CC-BY-4.0 | 署名 Manon Zuurmond，注明改动 | About 页 + 图注 + `ASSETS.csv` |
| **bioicons** 单图标 | CC0 / MIT / CC-BY 各自 | **逐个**引用作者与许可 | `ASSETS.csv` 逐行记录（Servier / DBCLS / TogoTV 等） |
| **3Dmol.js** | BSD-3-Clause（**F2：M0 复核 NOASSERTION**） | 保留版权声明 + 引用 Bioinformatics 论文 | About 页 + `CREDITS.md`；DOI 于 M0 补齐 |
| **Cantera** | **BSD-3-Clause（`License.txt` 原文已核，F1）** | 保留版权声明（含 Caltech / Sandia 政府权利声明） | `CREDITS.md` / About 页；可并入 LGPL-3.0 主链 |
| RDKit / RDKit.js | BSD-3-Clause | 保留版权声明 | About 页 |
| Lucide / Tabler / Iconify | ISC / MIT | 保留声明 | About 页 |
| Kenney | CC0 1.0（**M0 复核包内 LICENSE**） | 确认后入库 | `ASSETS.csv`；卡通器材不入库 |
| PubChem | 免费公开 | ≤ 5 req/s；批量走官方通道；引用来源 | 管线限流 + 物质卡 `source` 字段 |
| **NB实验室** | 闭源商业 | **不使用**其代码 / 素材 / 商标 / 界面 / 模板文案；不做破解或绕授权；**公开点名对标并以其为超越目标 + 独立开源实现·无关联声明**；NB 侧数据只用一级来源 | `CHARTER` 对标边界、统一口径 D、PR 模板勾选 |

### 3.5 CI 落地

```
license-scan（每次 PR 必跑）
  ├─ 扫描 pnpm-lock.yaml / Cargo.lock / requirements.lock
  ├─ 白名单外 → 失败；AGPL / GPLv2-only → 直接失败
  ├─ GPL-3.0 组件出现 → 告警并要求 ADR（选型决策不纳入）
  └─ 校验 assets/attribution/ASSETS.csv 覆盖全部入库资产
lgpl-link-check
  ├─ LGPL 库为动态链接、运行时可替换
  ├─ NOTICE 含显著声明与两份许可证全文引用
  └─ 允许逆向调试 / 修改版源码可得
docs-and-compliance
  ├─ LICENSE / LICENSE.GPL-3 / LICENSE.LGPL-3 / NOTICE 存在且未回退 Apache-2.0
  ├─ 决策台账存在；无明文 token；无 tikz 宏包源码
  └─ 内部链接有效
```

> **法律边界声明**：以上为工程判断，非法律意见。商业化前建议就 ① CC-BY-SA 衍生规则表边界 ② LPPL 输出物商用 ③ CC-BY 署名充分性 ④ 公开点名对标的比较广告合规 四项做法务确认。

## 四、性能预算（按 SP-1 帧预算，取代初版「热路径零 RTT」）

| 项 | 口径 | 依据 |
|---|---|---|
| 帧预算 | **16.7ms / 帧（60fps）**，表现层固定独立渲染 | ADR-0008 |
| 求解算力 | 按**关注度分数**动态配额；焦点内高频高精度、焦点外降频 / 粗粒度 / 冻结 / 缓存 | SP-1 第 2 层 |
| 数值自适应 | **SciPy LSODA/BDF** 局部误差 + `rtol`/`atol` 决定步长；内置刚性检测自动切 BDF ↔ Adams；**无硬编码时间阈值**（CVODES 后置 M1 可选加速） | SP-1 第 1 层 / D3 |
| 表现解耦 | 求解结果以「物种分布快照 + 时间戳」异步喂入，插值 / 外推平滑；**求解耗时不进入帧预算** | SP-1 第 3 层 |
| 事件唤醒 | 加料 / 加热 / 改参数 / pH 突变 / 时间轴跳转立即重算；稳态冻结复用缓存 | SP-1 第 4 层 |
| 带宽 | 服务端只推「快照 + 现象指令」，不推网格数据 | 表现解耦 |
| 求解器资源 | worker 级 CPU / 内存 / 单步超时上限；不收敛体系降级并告警 | `SECURITY.md` |
| 验收 | 焦点内**数值零错**；帧率恒 ≥ 60fps；焦点外算力随关注度单调下降；新增体系无需改调度代码 | ADR-0008 |

## 五、API 与部署的验收标准

| 检查 | 标准 |
|---|---|
| 最小部署 | 4C8G 单机 `docker compose up -d` 后浏览器可玩；**前后端常驻** |
| **双平台** | Windows 与 Linux **各跑一次**最小部署与资产转换，均通过 |
| 契约一致 | `/api/v1/solve` 与 WS `solve.result` 返回同一 `st.phenomenon.v1` 结构 |
| 数值零错 | 黄金用例全绿；焦点内 pH / 浓度 / 平衡 / 计量 / 方向与权威源一致 |
| 60fps | 重体系求解时容器内现象渲染不掉帧 |
| 物种可查 | 每容器 `solution_speciation` 可读，隐藏反应在时间轴可回放 |
| 存档 | 保存 → 分享链接 → 时间轴回放，结果与原实验一致（带 `ruleset_version`） |
| 许可证 | CI 白名单 + `lgpl-link-check` + 双文本校验通过；无 AGPL / GPLv2-only 依赖 |
| 安全 | 恶意参数 / 超长体系在隔离 worker 内超时终止，不影响服务 |
| **不做** | 断网可玩、离线规则包、多人协作、规则包工坊、教学端点（长线） |
