#!/usr/bin/env python3
"""安全初始化 workspace 最小目录骨架。

默认只创建目录，不覆盖任何已存在文件。
可选 --with-templates 仅在目标文件不存在时创建最小模板文件。
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Iterable

MIN_DIRS = [
    "memory",
    ".learnings",
    "context",
    "shared-context",
    "reviews",
]

OPTIONAL_DIRS = [
    "memory/tasks",
    "memory/incidents",
    "memory/decisions",
    "context/research",
    "context/refs",
]

TEMPLATES = {
    "MEMORY.md": "# MEMORY.md\n\n版本：{date}\n\n## 长期记忆边界\n\n这个文件只保存长期、稳定、会在后续会话持续影响判断与行为的内容。\n",
    ".learnings/ERRORS.md": "# ERRORS.md\n\n版本：{date}\n\n## 错误记录\n\n记录高价值错误模式、触发条件、影响和修正方法。\n",
    ".learnings/LEARNINGS.md": "# LEARNINGS.md\n\n版本：{date}\n\n## 经验记录\n\n记录用户纠正、环境经验和可复用做法。\n",
    ".learnings/PROMOTION_QUEUE.md": "# PROMOTION_QUEUE.md\n\n版本：{date}\n\n## 晋升候选\n\n记录候选规则，等待 review 后再决定是否进入核心文件。\n",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="为指定 workspace 安全创建最小目录骨架，不覆盖已有内容。"
    )
    parser.add_argument(
        "workspace",
        nargs="?",
        default=".",
        help="目标 workspace 根路径，默认当前目录。",
    )
    parser.add_argument(
        "--with-templates",
        action="store_true",
        help="额外创建缺失的最小模板文件，但绝不覆盖已有文件。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只输出将要创建或跳过的内容，不实际写入。",
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="写入模板文件时使用的版本日期，默认当天日期。",
    )
    return parser.parse_args()


def ensure_dirs(base: Path, rel_paths: Iterable[str], dry_run: bool) -> list[str]:
    logs: list[str] = []
    for rel in rel_paths:
        path = base / rel
        if path.exists():
            logs.append(f"EXISTS  dir  {rel}")
            continue
        if dry_run:
            logs.append(f"WOULD   dir  {rel}")
            continue
        path.mkdir(parents=True, exist_ok=True)
        logs.append(f"CREATED dir  {rel}")
    return logs


def ensure_templates(base: Path, date: str, dry_run: bool) -> list[str]:
    logs: list[str] = []
    for rel, template in TEMPLATES.items():
        path = base / rel
        if path.exists():
            logs.append(f"EXISTS  file {rel}")
            continue
        if dry_run:
            logs.append(f"WOULD   file {rel}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(template.format(date=date), encoding="utf-8")
        logs.append(f"CREATED file {rel}")
    return logs


def main() -> int:
    args = parse_args()
    base = Path(args.workspace).expanduser().resolve()
    if not base.exists():
        if args.dry_run:
            print("WOULD   dir  .")
        else:
            base.mkdir(parents=True, exist_ok=True)
            print("CREATED dir  .")
    elif not base.is_dir():
        raise SystemExit(f"目标路径不是目录: {base}")

    print(f"WORKSPACE {base}")
    for line in ensure_dirs(base, MIN_DIRS, args.dry_run):
        print(line)
    for line in ensure_dirs(base, OPTIONAL_DIRS, args.dry_run):
        print(line)

    if args.with_templates:
        for line in ensure_templates(base, args.date, args.dry_run):
            print(line)
    else:
        print("SKIPPED templates disabled")

    print("DONE safe workspace initialization complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
