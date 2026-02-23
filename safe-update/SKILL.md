---
name: safe-update
description: Update OpenClaw from source code. Supports custom project path and branch. Includes pulling latest branch, rebasing, building and installing, restarting service. Triggered when user asks to update OpenClaw, sync source, rebase branch, or rebuild.
---

# Safe Update

Update OpenClaw from source to the latest version while preserving local changes.

## ⚠️ Important Warnings

- This script performs **git rebase** and **git push --force** - may lose local changes if not properly committed
- Uses **npm i -g .** for global installation - may require sudo
- Uses **systemctl --user restart** - will restart the OpenClaw service
- **Backup your config before running!** (see below)

## Requirements

Required binaries (must be installed):
- `git`
- `npm` / `node`
- `systemctl` (for restarting gateway)

## Configuration

### Environment Variables (optional)

```bash
# Set custom project path (default: $HOME/projects/openclaw)
export OPENCLAW_PROJECT_DIR="/path/to/openclaw"

# Set custom branch (default: main)
# Common branches: main, feat/your-branch-name
export OPENCLAW_BRANCH="your-feature-branch"

# Enable dry-run mode (no actual changes)
export DRY_RUN="true"
```

### Or Pass as Arguments

```bash
./update.sh --dir /path/to/openclaw --branch your-branch
```

## Pre-run Checklist

Before running, complete these steps:

- [ ] **Backup config files**: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak`
- [ ] **Backup auth profiles** (if exist): `cp ~/.openclaw/agents/main/agent/auth-profiles.json ~/.openclaw/auth-profiles.json.bak`
- [ ] **Ensure git changes are committed** or stashed
- [ ] **Check you have internet connection** for git fetch

## Workflow

```bash
# 1. Enter project directory
cd /home/ubuntu/projects/openclaw

# 2. Backup config files (good practice before update!)
echo "=== Backing up config files ==="
mkdir -p ~/.openclaw/backups
BACKUP_SUFFIX=$(date +%Y%m%d-%H%M%S)

# Backup main config
cp ~/.openclaw/openclaw.json ~/.openclaw/backups/openclaw.json.bak.$BACKUP_SUFFIX
echo "✅ Backed up: openclaw.json"

# Backup auth profiles (if exists)
if [ -f ~/.openclaw/agents/main/agent/auth-profiles.json ]; then
  cp ~/.openclaw/agents/main/agent/auth-profiles.json \
     ~/.openclaw/backups/auth-profiles.json.bak.$BACKUP_SUFFIX
  echo "✅ Backed up: auth-profiles.json"
fi

echo "💡 Backups saved to: ~/.openclaw/backups/"
echo ""

# 3. Add upstream repository (if not added)
git remote add upstream https://github.com/openclaw/openclaw.git 2>/dev/null || true

# 4. Fetch upstream changes
git fetch upstream

# 5. Update target branch
git checkout $BRANCH
git merge upstream/$BRANCH

# 6. View changelog
echo "=== Full Changelog ==="
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v$(node -e 'console.log(require("./package.json").version)')")
echo "Current version: $CURRENT_TAG"
echo ""

# 7. Build and install
npm run build
npm i -g .

# 8. Check version
NEW_VERSION=$(openclaw --version)
echo "✅ Update complete! New version: $NEW_VERSION"
echo ""

# 9. Restart gateway
echo "=== Restarting Gateway ==="
systemctl --user restart openclaw-gateway

# 10. Verify Gateway health
echo "=== Checking Gateway Health ==="
sleep 3
if command -v openclaw &>/dev/null; then
  openclaw health 2>/dev/null || openclaw status
else
  echo "⚠️  openclaw command not available, please check Gateway status manually"
fi

# 11. Completion message
echo "=== Update Complete! ==="
echo ""
echo "✅ Workspace, memory, auth profiles are preserved automatically"
echo "✅ Backup is just a precaution - 30 seconds now vs. hours to rebuild"
echo "💡 If issues occur after update, restore from ~/.openclaw/backups/"
echo ""
```

## Quick Script

Run `scripts/update.sh` to automatically complete all steps above.

### Command Line Options

```bash
./update.sh [OPTIONS]

Options:
  --dir PATH       OpenClaw project directory (default: $HOME/projects/openclaw)
  --branch NAME    Git branch to update (default: main)
  --dry-run       Show what would be done without executing
  --help          Show this help message
```

### Examples

```bash
# Update with defaults
./update.sh

# Update specific branch
./update.sh --branch feat/my-branch

# Dry run (preview only)
./update.sh --dry-run

# Custom project path
./update.sh --dir /opt/openclaw --branch main
```

## Notes

- **Rebase may cause conflicts** - if conflicts occur, resolve manually and continue
- **Force push** - after rebase, if pushing to fork, use `git push --force`
- **Service restart** - gateway will restart, brief downtime expected
- **Backup first** - always backup before updating!

## Troubleshooting

### Git Conflicts During Rebase

```bash
# Resolve conflicts manually, then:
git add .
git rebase --continue
# Continue with build steps
```

### Build Fails

```bash
# Clean and retry:
rm -rf node_modules dist
npm install
npm run build
```

### Gateway Won't Start

```bash
# Check status:
systemctl --user status openclaw-gateway

# View logs:
journalctl --user -u openclaw-gateway -n 50
```
