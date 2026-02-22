---
name: safe-backup
description: Backup OpenClaw state directory and workspace. Includes excluding logs, sessions and other sensitive files, packaging for backup. Triggered when user asks to backup, export, or save state.
---

# Safe Backup

Backup OpenClaw state directory and workspace to GitHub.

## Quick Backup

```bash
/home/ubuntu/.openclaw/skills/safe-backup/scripts/backup.sh
```

## Backup Contents

- `~/.openclaw/` (state directory)
- `~/.openclaw/workspace/` (workspace)

## Excluded Files

- `*.log` log files
- `sessions.json` session files

## GitHub Backup Flow

1. **Initialize** (one-time):
   - Create a private repository on GitHub (e.g., `safe-backup`)
   - Clone locally: `git clone https://github.com/<your-username>/safe-backup.git`

2. **Each Backup**:
   - Run backup script to generate `tar.gz` file (e.g., `/tmp/safe-backup-20260222.tar.gz`)
   - Extract to cloned directory: `tar -xzf /tmp/safe-backup-20260222.tar.gz -C /path/to/safe-backup`
   - Commit and push: `cd /path/to/safe-backup && git add . && git commit -m "Backup 2026-02-22" && git push origin main`

**Note**: Extracting will overwrite old files. After git commit, GitHub will have the latest backup.

## Restore Flow

Reference: [Migration Guide](https://docs.openclaw.ai/en-US/install/migrating)
