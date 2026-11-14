# 07 · API 契约、部署与许可证合规矩阵

## 一、API 契约（gateway）

风格：REST（资源/查询/管理）+ WebSocket（实时现象、协作）+ 内部任务队列（冷路径）。全部返回 `protocol` 包定义的类型，`schema` 版本随响应头 `X-OCL-Schema-Version` 返回。

### 1.1 REST

| 方法 | 路径 | 用途 | 备注 |
|---|---|---|---|
| `GET` | `/api/v1/health` | 健康检查 | 最小部署探针 |
| `GET` | `/api/v1/compounds?q=&page=` | 化合物资料卡检索（名称/分子式/SMILES） | 走 PG |
| `GET` | `/api/v1/compounds/:id` | 资料卡详情（含结构 SVG、物性、GHS） | 可缓存 |
| `POST` | `/api/v1/compounds/search/structure` | 子结构/相似检索 | RDKit Cartridge |
| `GET` | `/api/v1/substances` / `materials` / `apparatus` | 试剂/材质/器材清单 | 前端启动拉取 |
| `GET` | `/api/v1/rules/:id` | 规则详情（含 source/confidence） | 图鉴用 |
| `POST` | `/api/v1/solve` | **组合求解**：`(substance[], conditions)` → 现象指令 | 热路径不调；温/冷路径用 |
| `GET` | `/api/v1/rulesets/:version` | 下载编译后的二进制规则包 | 启动时 + 版本更新 |
| `POST` | `/api/v1/saves` | 保存实验 | 返回 `save_id` |
| `GET` | `/api/v1/saves/:id` | 读取存档 | 分享链接 |
| `GET` | `/api/v1/saves/:id/replay` | 时间轴重放数据 | 教学回放 |
| `POST` | `/api/v1/uncovered` | 上报未命中组合 | 数据飞轮 |
| `GET` | `/api/v1/uncovered/stats` | 未覆盖统计（内容团队） | 按频次 |
| `POST` | `/api/v1/reports` | 生成实验报告（Markdown/PDF/CSV） | M3 |
| `GET` | `/api/v1/experiments` | 教材实验模板检索（章节/知识点/版本） | M3 |
| `POST` | `/api/v1/assessments` | 提交操作测评结果 / xAPI 语句 | M3 |
| `POST` | `/api/v1/lti/launch` | LTI 1.3 启动（ltijs） | M3 |
| `POST` | `/api/v1/rulesets/import` | 导入社区规则包（需审核） | M4 |

### 1.2 WebSocket

| 事件 | 方向 | 载荷 |
|---|---|---|
| `solve.request` | C→S | `{ request_id, substances[], conditions }`（仅本地规则包未命中时） |
| `solve.result` | S→C | 现象指令 或 `{fallback, hint}` |
| `solve.pending` | S→C | 冷路径入队提示（前端继续动画，不阻塞） |
| `phenomenon.push` | S→C | 教师端广播演示 / 协作同步 |
| `collab.update` | 双向 | Yjs CRDT 更新（M4） |
| `presence` | 双向 | 房间在线状态 |

> **契约要点**：`solve.result` 与本地规则引擎返回**同一种现象指令结构**（`ocl.phenomenon.v1`），前端无需区分来源。热路径零网络，冷路径异步不卡画面。

### 1.3 求解缓存键

```
key = sha256( sorted(substance_ids) + "|" + canonical(condition_buckets) + "|" + ruleset_version )
```

Redis LRU；命中率目标 > 95%（靠夜间预计算与未覆盖日志回灌）。

## 二、部署（Docker Compose）

### 2.1 服务清单

| 服务 | 端口 | 说明 | 最小部署 |
|---|---|---|---|
| `web` | 80 | Nginx 静态前端 + 资产 | 必需 |
| `gateway` | 3000 | REST + WS + 鉴权 | 必需 |
| `postgres` | 5432 | PG + RDKit Cartridge | 必需 |
| `redis` | 6379 | 缓存/会话 | 必需（单机可内嵌） |
| `chem-worker` | 内部 | 冷路径计算 | M2 起 |
| `precompute` | 内部 | 夜间规则编译 | M2 起 |
| `minio` | 9000 | 存档/规则包/截图 | 单机用本地卷 |
| `caddy` | 443 | 反代 + 自动 HTTPS | 可选 |

### 2.2 自托管步骤（M1 交付）

```bash
git clone https://github.com/stellarissss/open-chem-lab.git
cd open-chem-lab
cp deploy/.env.example .env          # 设置 POSTGRES_PASSWORD / JWT_SECRET / 域名
docker compose -f deploy/docker-compose.minimal.yml up -d
# 浏览器打开 http://<你的服务器> 即可玩；无需任何外部账号或云服务
```

### 2.3 环境要求（硬门槛）

| 项 | 最低 | 推荐 |
|---|---|---|
| CPU / 内存 | 4C / 8G | 8C / 16G |
| 磁盘 | 20 GB | 80 GB（含 PubChem 资料卡与 ORD 子集） |
| 系统 | Linux + Docker 24+ / Compose v2 | — |
| 网络 | 部署期需拉镜像与数据源；**运行期无需外网** | 离线可玩 |

### 2.4 数据与备份

- PG 每日 `pg_dump`；MinIO/本地卷快照；规则包版本化可回滚。
- 无状态服务可随时重建；`ruleset_version` 保证存档可解释。
- 升级流程：备份 → 拉新镜像 → 跑 DB migration（向前兼容）→ 灰度下发新规则包 → 回滚预案。

### 2.5 安全（自托管）

| 项 | 措施 |
|---|---|
| 认证 | 本地账号（argon2）+ 可选 OIDC / LTI；JWT 短期 + refresh |
| 传输 | Caddy 自动 HTTPS；WS 走 wss |
| 输入校验 | 所有 API 用 schema 校验；SMARTS/自定义规则在**沙箱进程**内解析，限制 CPU/内存与超时 |
| 社区规则包 | 必须审核 + 签名；默认 `confidence: community`，不进 `verified` 沙盒 |
| 内容安全 | 规则与存档是数据，不执行任意代码；需执行的地方（SMARTS）用隔离 worker |
| 依赖 | CI 许可证扫描 + 依赖漏洞扫描；锁定版本 |
| 隐私 | 学习数据留在自托管实例；xAPI LRS 可自托管；不上报第三方 |

## 三、许可证合规矩阵（**红线，CI 强制**）

### 3.1 主项目

| 项 | 值 |
|---|---|
| 主代码许可证 | **Apache-2.0**（ADR-0001） |
| 第三方组件 | 各自许可证保留，见 `CREDITS.md` / `assets/attribution/` |
| 内容数据 | 自有规则 Apache-2.0；ORD 衍生规则 CC-BY-SA-4.0 并独立署名 |

### 3.2 允许进入主构建产物的许可证（白名单）

`MIT` · `BSD-2-Clause` · `BSD-3-Clause` · `Apache-2.0` · `ISC` · `CC0-1.0` · `CC-BY-4.0`（需署名）· `PostgreSQL` · `Python-2.0`

### 3.3 禁止链接/合并（灰名单，仅参考或独立页面）

| 项目 | 许可 | 允许的方式 | 禁止的方式 |
|---|---|---|---|
| The Powder Toy | GPL-3.0 | 只读源码参考、独立自托管页面 | import / 链接 / 合并构建产物 / 移植代码进主仓 |
| tptmp | AGPL-3.0 | 只读参考 | 任何网络服务合并 |
| PhET sims | GPL | 独立页面原样自托管 | 定制后并入主代码库 |
| H5P core | GPL-3.0 | 独立进程/页面 | 并入主构建产物 |
| cdk (CDK) | LGPL-2.1 | 只读参考 | 静态链接进主产品 |
| Jmol-SwingJS | LGPL-2.1 | 只读参考 | 静态链接 |

> 若确需 LGPL 组件，只允许**动态链接 + 可替换**形态，并在法务确认后单独 ADR。

### 3.4 特殊资产与数据的处理义务

| 对象 | 许可证 | 义务 | 落地 |
|---|---|---|---|
| **tikz-chemlab** 宏包源码 | LPPL-1.3c | 不改源码、不随产品分发；只转译**编译输出物**（Clause 1 允许运行）；若改源码须按 Clause 6 改名+变更日志+附原件 | 构建期从 CTAN 拉取，源码不入库；`assets/attribution/` 署名 aihua + pst-labo 四作者 |
| **ord-data** | CC-BY-SA-4.0（数据）/ Apache-2.0（脚本） | 署名 + **相同方式共享**；衍生规则表保留 SA 声明 | `data-ord/` 独立仓；衍生规则标 `CC-BY-SA-4.0` 溯源；只抽取事实性反应式与条件，不整段复制描述文本 |
| **LabIcons** | CC-BY-4.0 | 署名 Manon Zuurmond，注明改动 | About 页 + 图注 + `ASSETS.csv` |
| **bioicons** 单图标 | CC0 / MIT / CC-BY 各自 | **逐个**引用作者与许可 | `ASSETS.csv` 逐行记录原始作者（Servier / DBCLS 等） |
| **3Dmol.js** | BSD-3-Clause | 保留版权声明 + 引用 Bioinformatics 论文 | About 页 + `CREDITS.md` |
| **RDKit / RDKit.js** | BSD-3-Clause | 保留版权声明 | About 页 |
| **Lucide** | ISC / **Tabler, Iconify** | 保留声明 | About 页 |
| **Kenney** | CC0 1.0（**待 M0 复核包内 LICENSE**） | 确认后入库 | `ASSETS.csv` |
| **PubChem** | 免费公开 | ≤ 5 req/s；批量走官方通道；引用来源 | 管线限流 + 资料卡 `source` 字段 |
| **NB实验室** | 闭源商业 | **不使用**其代码/素材/商标/界面/模板文案；不做破解或绕授权 | `CHARTER` 对标边界 + PR 模板勾选 |

### 3.5 CI 落地

```
license-scan（每次 PR 必跑）
  ├─ 扫描 pnpm-lock.yaml / Cargo.lock / requirements.lock
  ├─ 白名单外的许可证 → 失败
  ├─ 检测 GPL/AGPL/LGPL 依赖 → 失败并提示 ADR-0005
  └─ 校验 assets/attribution/ASSETS.csv 覆盖全部入库资产
```

> **法律边界声明**：以上为工程判断，非法律意见。商业化前建议就 ① CC-BY-SA 数据衍生规则表边界、② LPPL 输出物商用、③ CC-BY 资产署名充分性 三项做一次法务确认。

## 四、API 与部署的验收标准

| 检查 | 标准 |
|---|---|
| 最小部署 | 4C8G 单机 `docker compose up -d` 后浏览器可玩 |
| 离线 | 断网后仍可玩本地规则包覆盖的实验 |
| 契约一致 | 本地规则引擎与 `/api/v1/solve` 返回同一现象指令结构 |
| 冷路径 | 前端显示「计算中…」时粒子动画不卡顿 |
| 缓存 | 常见组合命中率 > 95%，无重复重计算 |
| 存档 | 保存→分享链接→重放，结果与原实验一致 |
| 许可证 | CI 白名单扫描通过；主构建产物无 GPL/AGPL 依赖 |
| 安全 | 恶意 SMARTS/规则包在隔离 worker 内超时终止，不影响服务 |
