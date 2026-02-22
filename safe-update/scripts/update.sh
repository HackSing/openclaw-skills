#!/bin/bash
# Safe Update Script
# Update OpenClaw from source

set -e

echo "=== Safe Update ==="
echo "Starting update process..."
echo ""

# 1. Enter project directory
cd /home/ubuntu/projects/openclaw

# 2. Backup config files
echo "=== Backing up config files ==="
mkdir -p ~/.openclaw/backups
BACKUP_SUFFIX=$(date +%Y%m%d-%H%M%S)
cp ~/.openclaw/openclaw.json ~/.openclaw/backups/openclaw.json.bak.$BACKUP_SUFFIX
echo "✅ Backed up: openclaw.json"

# 3. Add upstream
git remote add upstream https://github.com/openclaw/openclaw.git 2>/dev/null || true

# 4. Fetch and update
git fetch upstream
git checkout main
git merge upstream/main

# 5. Rebase feature branch
git checkout feat/allowed-agents-v2
git rebase main

# 6. Build and install
npm run build
npm i -g .

# 7. Restart gateway
systemctl --user restart openclaw-gateway

echo "✅ Update complete!"
