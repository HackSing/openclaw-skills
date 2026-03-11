#!/usr/bin/env python3
"""自包含的 EvoLoop 引导工具。

对外只保留两个子命令：
- init: 初始化 workspace 最小目录骨架与自我进化最小文件
- check: 检查 AGENTS.md 接管状态与自我进化骨架状态
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Iterable

MIN_DIRS = [
    "memory",
    ".learnings",
    ".learnings/pending",
    ".learnings/pending/archive",
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

INIT_FILES = {
    ".learnings/pending/rules.json": lambda version_date: {
        "version": version_date,
        "rules": [],
    },
    ".learnings/pending/info-sources.json": lambda version_date: {
        "version": version_date,
        "sources": [],
    },
}

AGENTS_MARKERS = [
    "SOUL.md",
    "MEMORY.md",
    ".learnings/pending/rules.json",
    "daily-review",
    "daily-info-update",
]

AGENTS_HEADING_KEYWORDS = [
    "检索顺序",
    "写入边界",
    "运行层",
]


def resolve_workspace(workspace: str, dry_run: bool) -> Path:
    base = Path(workspace).expanduser().resolve()
    if not base.exists():
        if dry_run:
            print("WOULD   dir  .")
        else:
            base.mkdir(parents=True, exist_ok=True)
            print("CREATED dir  .")
    elif not base.is_dir():
        print(f"错误：目标路径不是目录: {base}", file=sys.stderr)
        raise SystemExit(1)
    return base


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


def ensure_json_files(base: Path, version_date: str, dry_run: bool) -> list[str]:
    logs: list[str] = []
    for rel, factory in INIT_FILES.items():
        path = base / rel
        if path.exists():
            logs.append(f"EXISTS  file {rel}")
            continue
        if dry_run:
            logs.append(f"WOULD   file {rel}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(factory(version_date), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        logs.append(f"CREATED file {rel}")
    return logs


def _extract_headings(content: str) -> list[str]:
    """提取 markdown heading 文本（去掉 # 前缀）。"""
    headings: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            headings.append(stripped.lstrip("# ").strip())
    return headings


def check_agents_status(base: Path) -> list[str]:
    logs: list[str] = []
    filename = "AGENTS.md"
    path = base / filename
    if not path.exists():
        logs.append(f"MISSING file {filename}")
        return logs

    content = path.read_text(encoding="utf-8")
    headings = _extract_headings(content)
    headings_text = " ".join(headings)

    missing_markers = [m for m in AGENTS_MARKERS if m not in content]
    missing_headings = [kw for kw in AGENTS_HEADING_KEYWORDS if kw not in headings_text]
    all_missing = missing_markers + [f"heading:{kw}" for kw in missing_headings]

    if not all_missing:
        logs.append(f"OK      file {filename} (运行层规则已接管)")
        return logs

    logs.append(f"WARN    file {filename} (运行层规则可能未完整接管)")
    for marker in all_missing:
        logs.append(f"MISS    marker {marker}")
    return logs


def check_self_evolution(base: Path) -> list[str]:
    logs: list[str] = []

    for rel in [
        ".learnings/pending",
        ".learnings/pending/archive",
    ]:
        path = base / rel
        if path.is_dir():
            logs.append(f"OK      dir  {rel}")
        else:
            logs.append(f"MISSING dir  {rel}")

    rules_path = base / ".learnings/pending/rules.json"
    if not rules_path.exists():
        logs.append("MISSING file .learnings/pending/rules.json")
    else:
        try:
            data = json.loads(rules_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("rules"), list):
                logs.append("OK      file .learnings/pending/rules.json (valid top-level structure)")
            else:
                logs.append("WARN    file .learnings/pending/rules.json (invalid top-level structure)")
        except Exception as exc:  # noqa: BLE001
            logs.append(f"WARN    file .learnings/pending/rules.json (invalid json: {exc})")

    sources_path = base / ".learnings/pending/info-sources.json"
    if not sources_path.exists():
        logs.append("MISSING file .learnings/pending/info-sources.json")
    else:
        try:
            data = json.loads(sources_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("sources"), list):
                logs.append("OK      file .learnings/pending/info-sources.json (valid top-level structure)")
            else:
                logs.append("WARN    file .learnings/pending/info-sources.json (invalid top-level structure)")
        except Exception as exc:  # noqa: BLE001
            logs.append(f"WARN    file .learnings/pending/info-sources.json (invalid json: {exc})")

    return logs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="自包含的 EvoLoop 引导工具。"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init", help="初始化 workspace 最小目录骨架与自我进化最小文件。"
    )
    init_parser.add_argument(
        "workspace", nargs="?", default=".", help="目标 workspace 根路径，默认当前目录。"
    )
    init_parser.add_argument(
        "--dry-run", action="store_true", help="只输出将要创建或跳过的内容，不实际写入。"
    )
    init_parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="初始化 JSON 文件时使用的版本日期，默认当天日期。",
    )

    check_parser = subparsers.add_parser(
        "check", help="检查 AGENTS.md 接管状态与自我进化骨架状态。"
    )
    check_parser.add_argument(
        "workspace", nargs="?", default=".", help="目标 workspace 根路径，默认当前目录。"
    )

    extend_parser = subparsers.add_parser(
        "extend", help="创建可选子目录（memory/tasks、memory/incidents 等）。"
    )
    extend_parser.add_argument(
        "workspace", nargs="?", default=".", help="目标 workspace 根路径，默认当前目录。"
    )

    return parser


def run_init(args: argparse.Namespace) -> int:
    base = resolve_workspace(args.workspace, args.dry_run)
    print(f"WORKSPACE {base}")
    print("INIT    EvoLoop")
    for line in ensure_dirs(base, MIN_DIRS, args.dry_run):
        print(line)
    for line in ensure_json_files(base, args.date, args.dry_run):
        print(line)
    print("DONE init complete")
    return 0


def run_extend(args: argparse.Namespace) -> int:
    base = resolve_workspace(args.workspace, dry_run=False)
    print(f"WORKSPACE {base}")
    print("EXTEND  optional dirs")
    for line in ensure_dirs(base, OPTIONAL_DIRS, False):
        print(line)
    print("DONE extend complete")
    return 0


def run_check(args: argparse.Namespace) -> int:
    base = resolve_workspace(args.workspace, dry_run=False)
    print(f"WORKSPACE {base}")
    print("CHECK   AGENTS.md takeover status")
    for line in check_agents_status(base):
        print(line)
    print("CHECK   self-evolution status")
    for line in check_self_evolution(base):
        print(line)
    print()
    print("=" * 60)
    print("集成提示：")
    print("1. 读取当前 AGENTS.md，并先备份原文件。")
    print("2. 直接把 EvoLoop 的运行层最小规则写入 AGENTS.md。")
    print("3. 如缺少 pending 目录或 JSON 文件，执行：")
    print("   python3 ~/.openclaw/skills/EvoLoop/scripts/bootstrap.py init <workspace-root>")
    print("4. 完成后再次执行：")
    print("   python3 ~/.openclaw/skills/EvoLoop/scripts/bootstrap.py check <workspace-root>")
    print("=" * 60)
    print("DONE check complete")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init":
        return run_init(args)
    if args.command == "check":
        return run_check(args)
    if args.command == "extend":
        return run_extend(args)

    parser.error(f"未知命令: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
