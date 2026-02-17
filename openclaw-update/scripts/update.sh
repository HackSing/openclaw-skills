#!/bin/bash
# OpenClaw 源码更新脚本
# 用法: ./update.sh [branch]

set -e

PROJECT_DIR="/home/ubuntu/projects/openclaw"
DEFAULT_BRANCH="feat/add-token-usage-to-agent-end-hook"
BRANCH="${1:-$DEFAULT_BRANCH}"

echo "=== OpenClaw 源码更新 ==="
echo "功能分支: $BRANCH"
echo ""

# 1. 进入项目目录
cd "$PROJECT_DIR"

# 2. 更新 main 分支
echo "[1/5] 更新 main 分支..."
git checkout main
git pull origin main

# 3. 切回功能分支并 rebase
echo "[2/5] Rebase 到最新 main..."
git checkout "$BRANCH"
git rebase main

# 4. 构建并安装
echo "[3/5] 构建项目..."
npm run build

echo "[4/5] 安装到全局..."
npm i -g .

# 5. 重启 gateway
echo "[5/5] 重启 gateway..."
systemctl --user restart openclaw-gateway

echo ""
echo "=== 更新完成 ==="
echo "版本: $(openclaw --version)"
