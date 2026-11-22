# Windows / WSL2 部署指南

> 部署架构与双平台硬约束见 [01-Architecture.md](../docs/01-Architecture.md) 第二/六节。
> 官方依据：Microsoft Learn《Working across Windows and Linux file systems》。

## 1. 官方要点

Microsoft Learn 原文建议：

> "For the fastest performance speed, store your files in the WSL file system if you are working in a Linux command line (Ubuntu, OpenSUSE, etc)."

即项目文件放 **WSL2 发行版内部文件系统**（如 `\\wsl$\Ubuntu\home\<user>\open-chem-lab`），**不要**放在 `/mnt/c/...`（跨文件系统 bind mount 性能显著下降、权限/属主语义与 Linux 不一致）。

## 2. 前置条件

- Windows 10 21H2+ / Windows 11，已启用 WSL2：`wsl --install`（管理员 PowerShell），`wsl --set-default-version 2`
- Docker Desktop 安装时勾选 **Use the WSL 2 based engine**，并在 *Settings → Resources → WSL Integration* 启用目标发行版
- 在 **WSL2 终端内**（不是 PowerShell）执行下列所有命令
- 仓库克隆到 WSL2 原生路径：`git clone <repo> ~/open-chem-lab && cd ~/open-chem-lab`
  （凭据走 `git remote` 交互或凭据管理器，**不写入 `.git/config` 或任何入库文件**）

## 3. 起服

```bash
cp deploy/.env.example deploy/.env      # 按需修改端口与本地开发口令
docker compose -f deploy/docker-compose.minimal.yml up -d --build
```

默认 `docker compose up` 启动四个服务：`web` / `gateway` / `solver-worker` / `postgres`；`reaktoro-service` 为可选占位服务，需显式启用 `--profile reaktoro`。

## 4. 部署核验

| # | 命令 / 动作 | 期望结果 |
|---|---|---|
| 1 | `git config --get core.autocrlf` + `file deploy/*.yml` | 无 CRLF，`.gitattributes` 生效（LF） |
| 2 | `docker compose version` | v2.x（WSL2 引擎） |
| 3 | `docker compose -f deploy/docker-compose.minimal.yml config -q` | 语法通过、路径均为相对 LF |
| 4 | `docker compose -f deploy/docker-compose.minimal.yml up -d --build` | 四服务启动良好 |
| 5 | `curl -s localhost:8080` / `curl -s localhost:3001/api/v1/health` | HTTP 200 |
| 6 | `docker compose exec postgres pg_isready` | accepting connections |
| 7 | `docker compose exec solver-worker ls -la /app` | 属主、读写权限正常（非 `root:root` 只读） |
| 8 | `docker compose exec solver-worker python3 -c "import sys; print(sys.version)"` | Python 3.11 |
| 9 | reaktoro-service 内 `readelf -d ... \| grep libReaktoro`（启用 profile 后） | NEEDED `libReaktoro.so`（LGPL 动态链接） |
| 10 | 资产转换链：`lualatex → PDF → pdftocairo -svg` | 生成 SVG 且无字体依赖（见 [asset-pipeline](../tools/asset-pipeline/README.md)） |
| 11 | Chrome 打开前端，检查 3Dmol 分子视图 | WebGL 正常、球棍渲染可见 |

第 4–7 项是 Windows 侧最易出问题的环节（端口占用、卷挂载权限、跨文件系统性能），优先执行。

## 5. 常见坑与处置

| 坑 | 处置 |
|---|---|
| 把仓库放在 `/mnt/c/...` | 移到 WSL2 原生文件系统；跨 FS bind mount 慢且权限语义异常 |
| Windows 保留端口（Hyper-V 动态端口段常占用 3000/5000 段） | `netsh interface ipv4 show excludedportrange protocol=tcp` 查看，必要时在 Compose 改宿主端口映射 |
| CRLF 被编辑器写回 | 保持 `.gitattributes`；`git add --renormalize .`；IDE 设 LF |
| 路径大小写冲突 | Windows FS 不区分大小写，全仓保持 snake_case 小写 |
| WASM / 产物二进制被换行转换 | `.gitattributes` 已把 `*.wasm` / `*.png` 等标 `binary` |
| conda-forge `repodata.json` 超时 | reaktoro-service 镜像用 anaconda.org API 直取单包或锁定镜像，不在构建时全量 `conda solve` |
| TeX Live 字体在 WSL2 缺失 | 资产管线用 `pdftocairo -svg` 输出纯路径，不依赖系统字体 |

## 6. 停止

```bash
docker compose -f deploy/docker-compose.minimal.yml down
```
