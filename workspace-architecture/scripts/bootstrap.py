#!/usr/bin/env python3
"""自包含的 workspace-architecture 引导工具。

对外只保留一个脚本入口，但通过子命令明确区分职责：
- init: 初始化 workspace 最小目录骨架与自我进化最小文件
- check: 检查 AGENTS.md 的 frontmatter 状态与自我进化骨架状态
- patch: 创建 WORKSPACE-PATCH.md 规则补丁文件
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

PATCH_TEMPLATES = {
    "WORKSPACE-PATCH.md": """# WORKSPACE-PATCH.md

版本：{date}

## 用途

这是 workspace-architecture 技能的规则补丁文件。

**不要直接修改 AGENTS.md 的原有内容！**
而是通过 frontmatter 引用此文件，让 Agent 优先读取。

## 集成方式

在你的 AGENTS.md 最顶部添加：

```markdown
---
workspace-architecture-patch: ./WORKSPACE-PATCH.md
---
```

## 核心规则

### 1. 首次接管 workspace 检查

首次在一个 workspace 中使用时，先检查最小目录骨架：
- memory/
- .learnings/
- .learnings/pending/
- .learnings/pending/archive/
- context/
- shared-context/
- reviews/

如果缺失，通过本技能的 bootstrap.py init 子命令创建。

### 2. daily memory 读取规则

必须先读今天对应的 `memory/YYYY-MM-DD.md`，再读昨天对应的 `memory/YYYY-MM-DD.md`。

如果文件不存在，必须明确说明不存在，不要假装已经读取。

### 3. 自我进化规则

- 名称为 `daily-info-update` 和 `daily-review` 的 cron 任务发现候选规则时，必须先进入 `.learnings/pending/rules.json`
- `rules.json` 只保留 `pending`
- 其他状态通过名称为 `daily-review` 的 cron 任务立即归档到 `.learnings/pending/archive/`

### 4. 写入边界

- 资料型内容 → `context/`
- 错误和纠正 → `.learnings/`
- 长期稳定经验 → `MEMORY.md`

### 5. 不要直接修改用户原有文档

- 不要直接修改 AGENTS.md 的原有内容
- 通过 frontmatter 引用补丁文件
- 需要完整规则时读取：~/.openclaw/skills/workspace-architecture/SKILL.md

## 完整规则

完整规则请读取：~/.openclaw/skills/workspace-architecture/SKILL.md
""",
}


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


def ensure_patch(base: Path, version_date: str, dry_run: bool) -> list[str]:
    logs: list[str] = []
    for rel, template in PATCH_TEMPLATES.items():
        path = base / rel
        if path.exists():
            logs.append(f"EXISTS  file {rel}")
            continue
        if dry_run:
            logs.append(f"WOULD   file {rel}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(template.format(date=version_date), encoding="utf-8")
        logs.append(f"CREATED file {rel}")
    return logs


def check_frontmatter(base: Path) -> list[str]:
    logs: list[str] = []
    filename = "AGENTS.md"
    path = base / filename
    if not path.exists():
        logs.append(f"SKIP    file {filename} (not found)")
        return logs

    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    has_frontmatter = False
    has_patch_key = False

    if lines and lines[0].strip() == "---":
        has_frontmatter = True
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if line.strip().startswith("workspace-architecture-patch:"):
                has_patch_key = True
                break

    if has_frontmatter and has_patch_key:
        logs.append(f"OK      file {filename} (has frontmatter + patch key)")
    elif has_frontmatter:
        logs.append(f"WARN    file {filename} (has frontmatter but no patch key)")
    else:
        logs.append(f"MISSING file {filename} (no frontmatter)")
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
        description="自包含的 workspace-architecture 引导工具。"
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
        "check", help="检查 AGENTS.md 的 frontmatter 状态与自我进化骨架状态。"
    )
    check_parser.add_argument(
        "workspace", nargs="?", default=".", help="目标 workspace 根路径，默认当前目录。"
    )

    patch_parser = subparsers.add_parser(
        "patch", help="创建 WORKSPACE-PATCH.md 规则补丁文件。"
    )
    patch_parser.add_argument(
        "workspace", nargs="?", default=".", help="目标 workspace 根路径，默认当前目录。"
    )
    patch_parser.add_argument(
        "--dry-run", action="store_true", help="只输出将要创建或跳过的内容，不实际写入。"
    )
    patch_parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="写入补丁文件时使用的版本日期，默认当天日期。",
    )

    return parser


def run_init(args: argparse.Namespace) -> int:
    base = resolve_workspace(args.workspace, args.dry_run)
    print(f"WORKSPACE {base}")
    print("INIT    workspace-architecture")
    for line in ensure_dirs(base, MIN_DIRS, args.dry_run):
        print(line)
    for line in ensure_dirs(base, OPTIONAL_DIRS, args.dry_run):
        print(line)
    for line in ensure_json_files(base, args.date, args.dry_run):
        print(line)
    print("DONE init complete")
    return 0


def run_check(args: argparse.Namespace) -> int:
    base = resolve_workspace(args.workspace, dry_run=False)
    print(f"WORKSPACE {base}")
    print("CHECK   frontmatter status")
    for line in check_frontmatter(base):
        print(line)
    print("CHECK   self-evolution status")
    for line in check_self_evolution(base):
        print(line)
    print()
    print("=" * 60)
    print("集成提示：")
    print("1. 在 AGENTS.md 最顶部添加：")
    print("   ---")
    print("   workspace-architecture-patch: ./WORKSPACE-PATCH.md")
    print("   ---")
    print("2. 通过以下命令创建补丁文件：")
    print("   python3 ~/.openclaw/skills/workspace-architecture/scripts/bootstrap.py patch <workspace-root>")
    print("3. 如缺少 pending 目录或 JSON 文件，执行：")
    print("   python3 ~/.openclaw/skills/workspace-architecture/scripts/bootstrap.py init <workspace-root>")
    print("=" * 60)
    print("DONE check complete")
    return 0


def run_patch(args: argparse.Namespace) -> int:
    base = resolve_workspace(args.workspace, args.dry_run)
    print(f"WORKSPACE {base}")
    print("PATCH   workspace-architecture")
    for line in ensure_patch(base, args.date, args.dry_run):
        print(line)
    print()
    print("=" * 60)
    print("下一步：")
    print("1. 在 AGENTS.md 最顶部添加：")
    print("   ---")
    print("   workspace-architecture-patch: ./WORKSPACE-PATCH.md")
    print("   ---")
    print("2. 使用以下命令检查集成与自我进化骨架状态：")
    print("   python3 ~/.openclaw/skills/workspace-architecture/scripts/bootstrap.py check <workspace-root>")
    print("=" * 60)
    print("DONE patch complete")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init":
        return run_init(args)
    if args.command == "check":
        return run_check(args)
    if args.command == "patch":
        return run_patch(args)

    parser.error(f"未知命令: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
