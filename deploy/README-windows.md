# Windows 侧最小部署 · 可执行补验清单

> **状态**：Linux 侧已实测通过（Docker Compose 4 服务全 Healthy，历史证据见 `docs/归档/research/04-M0验证报告.md` §2）；
> **Windows 实机起服在本沙箱（Ubuntu）无法覆盖**，按历史流程 `docs/归档/12-阶段二开发流程.md` 显式标「受限」，本清单交付用户在 Windows / WSL2 本机执行。
> 依据：台账 9.1（Win + Linux 双平台兼容）、D6（单机自托管）、D2（reaktoro-service 独立微服务）、
> [Microsoft Learn《Working across Windows and Linux file systems》](https://learn.microsoft.com/en-us/windows/wsl/filesystems) 一手核实（2026-11-15）。

---

## 0. 为什么需要这份清单

阶段二质量闸门把「双平台」定义为 **Linux 实测 + Windows 静态规范核查**；无法实机覆盖的部分必须显式标注并给出补验方案，不得写成「通过」。
静态核查（本沙箱已完成）：

| 检查 | 结果 |
|---|---|
| `.gitattributes` 强制 `* text=auto eol=lf` | ✅ |
| 含 CRLF 的文件数 | **0** |
| 文件名含 Windows 非法字符 `: * ? " < > \|` | **0** |
| 路径大小写冲突（同名不同大小写） | **0** |

静态层面已满足双平台红线；剩下的是**只能在真实 Windows 环境验证的运行时行为**。

---

## 1. 官方要点（一级来源，原文核实）

Microsoft Learn《Working across Windows and Linux file systems》：

> "We recommend against working across operating systems with your files, unless you have a specific reason for doing so.
> **For the fastest performance speed, store your files in the WSL file system if you are working in a Linux command line** (Ubuntu, OpenSUSE, etc)."

即：项目文件放 **WSL2 发行版内部文件系统**（如 `\\wsl$\Ubuntu\home\<user>\open-chem-lab`），
**不要**放在 `/mnt/c/...`（跨文件系统 bind mount 性能显著下降、且文件权限/属主语义与 Linux 不一致）。

---

## 2. 前置条件

- Windows 10 21H2+ / Windows 11，已启用 WSL2：`wsl --install`（管理员 PowerShell），`wsl --set-default-version 2`
- Docker Desktop 安装时勾选 **Use the WSL 2 based engine**，并在 *Settings → Resources → WSL Integration* 启用目标发行版
- 在 **WSL2 终端内**（不是 PowerShell）执行下列所有命令
- 仓库克隆到 WSL2 原生路径：`git clone <repo> ~/open-chem-lab && cd ~/open-chem-lab`
  （PAT 只走 `git remote` 交互或凭据管理器，**绝不写入 `.git/config` 或任何入库文件**）

---

## 3. 逐项补验（每条都对应 M0 验证清单的一项）

| # | 命令 / 动作 | 通过标准 | 对应风险 |
|---|---|---|---|
| 1 | `git config --get core.autocrlf` + `file deploy/*.yml` | 无 CRLF；`.gitattributes` 生效 | 换行符 |
| 2 | `docker compose version` | v2.x（WSL2 引擎） | 引擎 |
| 3 | `docker compose -f deploy/docker-compose.yml config -q` | 语法通过、路径均为相对 LF | Compose 可移植性 |
| 4 | `docker compose up -d` | `web / gateway / solver-worker / postgres / reaktoro-service` 全部 healthy | 服务编排 |
| 5 | `curl -s localhost:8080` / `curl -s localhost:3000/api/v1/health` | HTTP 200 | 端口占用（Windows 侧常见 3000/8080 冲突） |
| 6 | `docker compose exec postgres pg_isready` | accepting connections | 卷挂载 / 权限 |
| 7 | 卷挂载检查：`docker compose exec solver-worker ls -la /app` | 属主、读写权限正常（无 `root:root` 只读） | WSL ↔ Windows 权限 |
| 8 | `python3 -c "import phreeqpython; print(phreeqpython.__version__)"`（在 solver-worker 内） | 正常导入 | conda/pip 平台二进制 |
| 9 | reaktoro-service 内 `readelf -d ... \| grep libReaktoro` | NEEDED `libReaktoro.so` | LGPL 动态链接（M0 已在 Linux 实证） |
| 10 | 资产转换链：`lualatex → PDF → pdftocairo -svg` | 生成 SVG 且无字体依赖 | TeX Live 在 WSL2 的路径 / 字体 |
| 11 | Chrome 打开前端，检查 3Dmol 分子视图 | WebGL 正常、球棍渲染可见 | 真实 GPU（非 SwiftShader） |

> 第 4–7 项是 Windows 侧最容易出问题的地方（端口占用、卷挂载权限、跨文件系统性能），请优先执行。

---

## 4. 已知坑与处置（避免重复踩）

| 坑 | 处置 |
|---|---|
| 把仓库放在 `/mnt/c/...` | 移到 WSL2 原生文件系统；跨 FS bind mount 慢且权限语义异常 |
| Windows 保留端口（Hyper-V 动态端口段常占用 3000/5000 段） | `netsh interface ipv4 show excludedportrange protocol=tcp` 查看，必要时在 Compose 改宿主端口映射 |
| CRLF 被编辑器写回 | 保持 `.gitattributes`；`git add --renormalize .`；IDE 设 LF |
| 路径大小写不敏感 | Windows FS 不区分大小写，务必保持全仓 `snake_case` + 小写（静态核查已确认 0 冲突） |
| WASM / TeX 产物的二进制被换行转换 | `.gitattributes` 已把 `*.wasm` / `*.png` 等标 `binary` |
| conda-forge `repodata.json` 超时（本轮 Linux 实测全通道卡住） | reaktoro-service 镜像用 **anaconda.org API 直取单包**或锁定的 conda 镜像，勿在构建时 `conda solve` 全量 repodata |
| TeX Live 字体在 WSL2 缺失 | 资产管线只用 `pdftocairo -svg` 输出纯路径（M0 已实测零 `<text>`/零外部字体），不依赖系统字体 |

---

## 5. 回填

执行后请把结果（逐项 PASS/FAIL + `docker compose ps` 输出 + 截图）回填到 `docs/02-Roadmap.md`（当前进度），
把「Windows 实机受限」更新为实测结论；**未执行前不得写成「通过」**。

---

> 本清单只解决「Windows 运行时行为」这一项环境受限，不引入新的技术选型不确定性：
> 所有组件（Compose / Fastify / phreeqpython / reaktoro-service / pdftocairo）在 Linux 侧均已实测，
> 且均为跨平台成熟成品，Windows 侧的风险是部署环境差异，不是可行性问题。
