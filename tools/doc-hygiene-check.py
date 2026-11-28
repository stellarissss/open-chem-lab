#!/usr/bin/env python3
"""文档纯净检查：把「现行文档无过程痕迹、无并存状态、只含正向规格」变成机器判定。

维护目标（面向现行文档）：
- 每份文档只含正向规格与当前状态，过程叙事留给 git log。
- 每份 spec 只保留唯一现行状态，状态声明与状态区保持一致。

检查范围：AGENTS.md、docs/01-Architecture.md、docs/02-Roadmap.md、
docs/03-DocDD-Process.md、docs/specs/*.md、README.md、CONTRIBUTING.md、SECURITY.md。

判定规则（正向表述即通过）：
1. specs 每份只有单一现行状态：状态区（文末「## 状态」）唯一；正文不再夹带旧状态声明。
2. 现行文档不含过程痕迹词（见 PROCESS_MARKERS）。
3. spec 状态行与状态区一致（粗稿在顶部声明，正式稿在文末声明，二者不共存于同一文件）；
   正文「状态：X」只允许四态词，其他取值视为逃逸状态声明。
4. 01 §5.1「现行实体」表中的每个实体，必须在 schemas/ 有对应 *.v1.schema.json
   （防未来契约冒充现行；规划中实体单列不检查）。

能力边界（勿高估本门禁）：以上均为**字面/结构级**检查。语义级问题——目标冒充现状、
跨文档状态语气不一致、承诺与实现脱节——本门禁抓不住，须靠 03 §2.3 回写前查漏与人工审查。
本门禁通过 ≠ 文档已语义自洽。

用法：python3 tools/doc-hygiene-check.py [repo_root]
依赖：仅标准库。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# 过程痕迹词：执行叙事、临时状态、占位符，均不属正向规格。
PROCESS_MARKERS = [
    "已还原", "已完成快照落盘", "TODO", "FIXME", "波折", "临时方案",
    "刚发现", "修复了", "临时占位", "待补（执行",
]
# 状态词：出现在正文（非状态区）即为夹带声明。
STATUS_WORDS = ["粗稿", "待开始", "进行中", "已完成"]

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"[doc-hygiene] FAIL {msg}", file=sys.stderr)


def find_root(start: Path) -> Path:
    """向上查找含 AGENTS.md 与 docs/ 的仓库根。"""
    for candidate in [start, *start.parents]:
        if (candidate / "AGENTS.md").is_file() and (candidate / "docs").is_dir():
            return candidate
    return start


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else find_root(Path(__file__).resolve().parent)
    targets = [root / "AGENTS.md", root / "docs" / "01-Architecture.md",
               root / "docs" / "02-Roadmap.md", root / "docs" / "03-DocDD-Process.md",
               root / "README.md", root / "CONTRIBUTING.md", root / "SECURITY.md"]
    targets += sorted((root / "docs" / "specs").glob("*.md"))
    print(f"[doc-hygiene] root: {root}")

    for path in targets:
        if not path.is_file():
            fail(f"缺失现行文档 {path.relative_to(root)}")
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root)

        # 规则 2：过程痕迹词
        for marker in PROCESS_MARKERS:
            for m in re.finditer(re.escape(marker), text):
                line = text[: m.start()].count("\n") + 1
                fail(f"{rel}:{line} 含过程痕迹词「{marker}」")

        # 规则 1+3：spec 状态单一且一致
        if path.parent.name == "specs":
            # 文末状态区的值
            status_section = re.search(r"^## 状态\s*$\n+(.+?)(?:\n\n|\Z)", text, re.MULTILINE | re.DOTALL)
            section_val = None
            if status_section:
                for w in STATUS_WORDS:
                    if w in status_section.group(1):
                        section_val = w
                        break
            if section_val is None:
                fail(f"{rel}: 文末状态区缺失或无法识别状态")

            # 顶部夹带状态声明（> **状态：X** 或 状态：X）——与状态区并存即冲突
            head = text.split("## 状态")[0]
            inline = re.findall(r"状态[：:]\s*\**\s*(粗稿|待开始|进行中|已完成)", head)
            for val in inline:
                if section_val and val != section_val:
                    fail(f"{rel}: 正文状态「{val}」与状态区「{section_val}」并存")

            # 状态逃逸：正文「状态：X」只允许四态词，其他取值一律拦截
            for m in re.finditer(r"状态[：:]\s*\**\s*([^，。；\s]+)", head):
                raw = m.group(1)
                if raw.strip("「」*") not in STATUS_WORDS:
                    fail(f"{rel}: 正文夹带无法识别的状态声明「状态：{raw}」（只允许 {'/'.join(STATUS_WORDS)}）")

    # 规则 4：01 §5.1 现行实体 ↔ schemas/ 对应（规划实体单列、不检查）
    arch = (root / "docs" / "01-Architecture.md").read_text(encoding="utf-8")
    if "### 5.1" in arch:
        section = arch.split("### 5.1", 1)[1]
        current_part = section.split("**规划中实体", 1)[0]
        declared = set(re.findall(r"^\|\s*`([a-z_]+)`\s*\|", current_part, re.MULTILINE))
        published = {p.name.replace(".v1.schema.json", "") for p in (root / "schemas").glob("*.v1.schema.json")}
        for entity in sorted(declared - published):
            fail(f"01 §5.1 现行实体「{entity}」在 schemas/ 无对应文件（应移入规划段或先发 schema）")
        print(f"[doc-hygiene] 实体核对：§5.1 现行 {len(declared)} 个，schemas 已发布 {len(published)} 个")
    else:
        fail("01-Architecture.md 缺 §5.1 节")

    if errors:
        print(f"[doc-hygiene] 失败 {len(errors)} 项", file=sys.stderr)
        return 1
    print(f"[doc-hygiene] 通过：{len(targets)} 份现行文档状态单一、无过程痕迹、只含正向规格")
    print("[doc-hygiene] 注意：本门禁仅字面/结构级检查，语义级矛盾须靠回写查漏与人工审查")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
