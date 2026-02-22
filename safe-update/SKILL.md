---
name: safe-update
description: Update OpenClaw from source code. Includes pulling latest main branch, rebasing feature branch, building and installing, restarting service. Triggered when user asks to update OpenClaw, sync source, rebase branch, or rebuild.
---

# Safe Update

Update OpenClaw from source to the latest version while preserving local changes.

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

# 5. Update main branch
git checkout main
git merge upstream/main

# 6. View full changelog (friendly summary)
echo "=== Full Changelog ==="
# Get current and previous version tags
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v$(node -e 'console.log(require("./package.json").version)')")
PREV_TAG=$(git tag --sort=-creatordate | grep -A1 "^$CURRENT_TAG$" | tail -n1)
if [ "$PREV_TAG" = "$CURRENT_TAG" ]; then
  PREV_TAG=$(git tag --sort=-creatordate | grep -A2 "^$CURRENT_TAG$" | tail -n1)
fi

echo "Current version: $CURRENT_TAG"
echo "Previous version: $PREV_TAG"
echo ""
echo "--- Git Commits ---"
if [ -n "$PREV_TAG" ] && [ "$PREV_TAG" != "$CURRENT_TAG" ]; then
  git log "$PREV_TAG..HEAD" --oneline --no-decorate
else
  git log --oneline --no-decorate -50
fi
echo ""
echo "--- CHANGELOG Details ---"
# Find current version section in CHANGELOG
if [ -f CHANGELOG.md ]; then
  CHANGELOG_CONTENT=$(awk '/^## [0-9]/{p=0} /^## '${CURRENT_TAG#v}'/{p=1} p' CHANGELOG.md)
  echo "$CHANGELOG_CONTENT"
  echo ""
  echo "--- Summary of Major Changes ---"
  # Simple summary
  echo "$CHANGELOG_CONTENT" | awk '/^## /{p=0} /^### Changes/{p=1} p' | head -100 | sed 's/^- /*/'
fi

# 7. Switch to feature branch and rebase
git checkout feat/allowed-agents-v2
git rebase main

# 8. Build and install
npm run build
npm i -g .

# 9. Check version
NEW_VERSION=$(openclaw --version)
echo "✅ Update complete! New version: $NEW_VERSION"
echo ""

# 10. Verify config migration
echo "=== Verifying Config Migration ==="
echo "Checking model fallback chain..."
cat ~/.openclaw/openclaw.json | grep -A 10 '"model"' || echo "⚠️  Model config not found (may be normal)"
echo ""

# 11. Restart gateway
echo "=== Restarting Gateway ==="
systemctl --user restart openclaw-gateway

# 12. Verify Gateway health
echo "=== Checking Gateway Health ==="
sleep 3  # Wait for Gateway to start
if command -v openclaw &>/dev/null; then
  openclaw health 2>/dev/null || openclaw status
else
  echo "⚠️  openclaw command not available, please check Gateway status manually"
fi
echo ""

# 13. Completion message
echo "=== Update Complete! ==="
echo ""
echo "✅ Workspace, memory, auth profiles are preserved automatically"
echo "✅ Backup is just a precaution - 30 seconds now vs. hours to rebuild"
echo "💡 If issues occur after update, restore from ~/.openclaw/backups/"
echo ""
```

## Quick Script

Run `scripts/update.sh` to automatically complete all steps above.

## Notes

- After rebase, if pushing to fork, use `git push --force`
- After build, need to restart gateway to take effect
