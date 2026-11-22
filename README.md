# ST Crucible · 《ST实验室》

> **一个专业、好玩的开源仿真化学实验室。** 只做实验台，一切按实验室规格来；对标并超越闭源产品「NB实验室」。
> 仓库名 `open-chem-lab` ≠ 产品名。

[![License](https://img.shields.io/badge/License-LGPL%203.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%2B%20Linux-green.svg)](docs/01-Architecture.md)

---

## 这是什么

一个**开源、可自建服务器部署**的交互式仿真化学实验室：在实验台上按实验室规格取用真实器材与药品、自由组合、调节参数，即时看到变色、沉淀、气泡、燃烧、结晶、温度与 pH 曲线等现象；**错误操作的后果（密闭加热炸裂、浓硫酸稀释飞溅、钠入水爆燃）可零风险重现**。

它不是落沙游戏，也不提供虚构物质、自制规则或 MOD 工坊。「超自由」的精确含义：

> **在 100% 真实、已验算的物质与器材之上，由真实物理化学法则驱动的无限组合、涌现与自由探索。**

产品定义、技术栈、能力清单、红线与对标口径的完整权威表述见 **[docs/01-Architecture.md](docs/01-Architecture.md)**；进度见 **[docs/02-Roadmap.md](docs/02-Roadmap.md)**；开发流程见 **[docs/03-DocDD-Process.md](docs/03-DocDD-Process.md)**。

## 快速开始

仓库提供可运行的产品骨架（前后端常驻 + Docker Compose 单机自托管）：

```bash
# 1. 构建并起服（仓库根执行；需 Node 20.19+ / pnpm 10 / Docker）
cp deploy/.env.example deploy/.env        # 按需修改端口与本地开发口令
docker compose -f deploy/docker-compose.minimal.yml up -d --build

# 2. 浏览器打开 http://localhost:8080 —— 实验台壳页显示后端 health=OK
#    网关 health: curl http://localhost:3001/api/v1/health
#    停止: docker compose -f deploy/docker-compose.minimal.yml down

# 开发者本地构建（不起容器）：
pnpm install && pnpm build
python3 tests/license-scan/scan.py        # 依赖许可证白名单门禁
```

> 当前骨架不含真实化学体系与求解逻辑，按 [docs/02-Roadmap.md](docs/02-Roadmap.md) 逐片接入。AI/开发者入口按 `AGENTS.md` → `docs/02-Roadmap.md` → `docs/01-Architecture.md` → `docs/03-DocDD-Process.md` → `docs/specs/` 顺序。

## 文档导航

| 文档 | 内容 |
|---|---|
| [AGENTS.md](AGENTS.md) | AI 第一站：现场指针、当前焦点、硬约束 |
| [docs/01-Architecture.md](docs/01-Architecture.md) | **唯一技术真理源**：产品定义、技术栈、数据模型、红线、验证原则 |
| [docs/02-Roadmap.md](docs/02-Roadmap.md) | 当前进度、阶段、薄切片清单、下一步 |
| [docs/03-DocDD-Process.md](docs/03-DocDD-Process.md) | 开发流程：任务闭环、spec 写法、无强制门禁、变更分级 |
| [docs/specs/](docs/specs/) | 切片规格：已完成 spec + 下一切片粗稿 |
| [CREDITS.md](CREDITS.md) / [NOTICE](NOTICE) | 开源依赖致谢、逐项许可证、LGPL 显著声明 |
| [deploy/README-windows.md](deploy/README-windows.md) | Windows / WSL2 部署指南 |

## 许可证与免责

- **本项目代码**：[LGPL-3.0](LICENSE)（`LICENSE` + `LICENSE.GPL-3` + `LICENSE.LGPL-3` 三份构成完整交付）。第三方组件与数据各保留原许可证，见 [CREDITS.md](CREDITS.md)、[NOTICE](NOTICE)、`assets/attribution/`。
- **库可替换**：LGPL 库以动态链接、运行时可替换形态接入，允许自用修改、替换与逆向调试。
- **科学准确性**：事实层以数值零错为红线；本产品用于教学与自由探索，**不是实验级数据源**；界面常驻「现实操作勿模仿」。
- **商标与对标**：NB实验室/NOBOOK 为北京乐步教育科技有限公司产品与商标。本项目为独立开源实现，**与其无关联无背书**，不使用其代码/素材/界面/文案/商标；对标措辞与合规口径见 [docs/01-Architecture.md](docs/01-Architecture.md) 第七节。
- 合规分析为工程判断、非法律意见；商业化前法务确认事项见 [CREDITS.md](CREDITS.md)。

如果这些开源项目帮到了你，**请去给它们点个 ⭐** —— 开源生态靠这个运转。
