#!/bin/bash
# Safe Backup Script
# Backup state directory and workspace to GitHub

set -e

GITHUB_REPO="https://github.com/HackSing/clawdata.git"
BACKUP_DIR="/tmp/safe-backup-$(date +%Y%m%d)"
STATE_DIR="$HOME/.openclaw"
WORKSPACE_DIR="$HOME/.openclaw/workspace"

echo "=== Safe Backup ==="
echo "Time: $(date)"
echo ""

# 1. Create temporary backup directory
echo "[1/4] Creating backup directory..."
mkdir -p "$BACKUP_DIR"

# 2. Copy state directory (exclude sensitive files)
echo "[2/4] Copying state directory..."
rsync -av --exclude='*.log' --exclude='sessions.json' "$STATE_DIR/" "$BACKUP_DIR/state/"

# 3. Copy workspace
echo "[3/4] Copying workspace..."
cp -r "$WORKSPACE_DIR" "$BACKUP_DIR/workspace/"

# 4. Package
echo "[4/4] Packaging backup..."
cd /tmp
tar -czf safe-backup-$(date +%Y%m%d).tar.gz safe-backup-$(date +%Y%m%d)

echo ""
echo "=== Backup Complete ==="
echo "Backup file: /tmp/safe-backup-$(date +%Y%m%d).tar.gz"
echo ""
echo "Next steps (manual):"
echo "1. Create a private GitHub repository"
echo "2. git clone repository locally"
echo "3. Extract and commit backup"
