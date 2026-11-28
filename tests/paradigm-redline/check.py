#!/usr/bin/env python3
"""范式红线门禁（008）：静态扫描 web-ui，禁止旧演示层以任何形式复活。

红线依据 01 §7.1 / §一：禁预设配比、预设反应单元、实验会话、按钮化操作、
写死数值冒充操作；一切以物质为本体、手动操作、实时求解。本门禁把「范式偏移」
从文档约定变成机器判定——任何 Agent 想加回预设按钮/体积滑条/时间轴/报告入口，
都会在这里红灯。

判定规则（正向即通过）：
1. web-ui/src 不含旧演示层标识：PRESETS / solveHeat / 错误操作两按钮 /
   loadTimeline / /api/v1/timeline / generateReport / Report 组件 / Timeline 组件 /
   REAGENTS 硬编码表 / 加入顺序下拉 / 体积滑条。
2. 不含求解库直连或硬编码求解端口（沿用 spec-007 静态护栏）。
3. 正向存在新范式标识：临近交互范式、倾角物理、container_state 定向订阅、
   从 ruleset 派生的 catalog 取数。

用法：python3 tests/paradigm-redline/check.py [repo_root]
依赖：仅标准库。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

errors: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"[paradigm-redline] FAIL {msg}", file=sys.stderr)


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "AGENTS.md").is_file() and (candidate / "packages").is_dir():
            return candidate
    return start


# 旧演示层标识：正则 → 说明。命中任一即范式回潮。
FORBIDDEN = [
    (r"\bPRESETS\b", "预设配比下拉"),
    (r"\bsolveHeat\b", "写死热参数按钮"),
    (r"\bloadTimeline\b|\bSpeciationTimeline\b|/api/v1/timeline", "预置时间轴回放"),
    (r"\bgenerateReport\b|/api/v1/report|from\s+[\"']./Report[\"']", "实验报告入口"),
    (r"\bREAGENTS\b", "硬编码药品架"),
    (r"\bselectedVolume_L\b|取用体积|type=[\"']range[\"'][^>]*体积", "体积滑条"),
    (r"\badditionOrder\b|加入顺序", "二选一顺序下拉"),
    (r"\b水入浓酸\b|\b浓酸入水\b", "错误操作演示按钮"),
    (r"8765|localhost:\d{4}|127\.0\.0\.1:\d{4}", "硬编码求解端口"),
    (r"from\s+[\"']st_solver_worker|import\s+phreeqpython", "web-ui 直连求解库"),
]

# 新范式正向标识：至少各出现一处（防止空实现蒙混）。
REQUIRED = [
    (r"nearby-action|detectNearby|临近交互", "临近交互范式"),
    (r"tiltFromPointer|criticalAngleDeg|flowRate|倾角", "倾角倾倒物理"),
    (r"container_state", "容器状态定向订阅"),
    (r"/api/v1/bench/catalog", "ruleset 驱动的目录取数"),
    (r"rotate\(.*rotation|rotate\(.*tilt|liquidCounterRotation", "液面水平反向旋转"),
]


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else find_root(Path(__file__).resolve().parent)
    ui_src = root / "packages" / "web-ui" / "src"
    if not ui_src.is_dir():
        fail(f"缺失 {ui_src.relative_to(root)}")
        return 1

    texts: list[tuple[Path, str]] = []
    for p in sorted(ui_src.rglob("*")):
        if p.is_file() and p.suffix in {".ts", ".tsx", ".js", ".jsx"}:
            texts.append((p, p.read_text(encoding="utf-8", errors="ignore")))
    if not texts:
        fail("web-ui/src 无源码文件")
        return 1

    for path, text in texts:
        rel = path.relative_to(root)
        for pattern, label in FORBIDDEN:
            if re.search(pattern, text):
                fail(f"{rel} 命中范式红线：{label}（正则 {pattern}）")

    whole = "\n".join(t for _, t in texts)
    for pattern, label in REQUIRED:
        if not re.search(pattern, whole):
            fail(f"缺少新范式正向标识：{label}（正则 {pattern}）")

    if errors:
        print(f"[paradigm-redline] 失败 {len(errors)} 项", file=sys.stderr)
        return 1
    print(f"[paradigm-redline] 通过：扫描 {len(texts)} 个前端源码，无旧演示层残留，新范式标识齐备")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
