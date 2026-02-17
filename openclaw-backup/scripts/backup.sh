#!/bin/bash
# OpenClaw 备份脚本
# 备份状态目录和工作区到 GitHub

set -e

GITHUB_REPO="https://github.com/HackSing/clawdata.git"
BACKUP_DIR="/tmp/openclaw-backup-$(date +%Y%m%d)"
STATE_DIR="$HOME/.openclaw"
WORKSPACE_DIR="$HOME/.openclaw/workspace"

echo "=== OpenClaw 备份 ==="
echo "时间: $(date)"
echo ""

# 1. 创建临时备份目录
echo "[1/4] 创建备份目录..."
mkdir -p "$BACKUP_DIR"

# 2. 复制状态目录（排除敏感文件）
echo "[2/4] 复制状态目录..."
rsync -av --exclude='*.log' --exclude='sessions.json' "$STATE_DIR/" "$BACKUP_DIR/state/"

# 3. 复制工作区
echo "[3/4] 复制工作区..."
cp -r "$WORKSPACE_DIR" "$BACKUP_DIR/workspace/"

# 4. 打包
echo "[4/4] 打包备份..."
cd /tmp
tar -czf openclaw-backup-$(date +%Y%m%d).tar.gz openclaw-backup-$(date +%Y%m%d)

echo ""
echo "=== 备份完成 ==="
echo "备份文件: /tmp/openclaw-backup-$(date +%Y%m%d).tar.gz"
echo ""
echo "下一步手动操作:"
echo "1. 创建 GitHub 私人仓库"
echo "2. git clone 仓库到本地"
echo "3. 解压并提交备份"
