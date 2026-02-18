---
name: openclaw-update
description: 从源码更新 OpenClaw。包括拉取最新 main 分支、rebase 功能分支、构建安装、重启服务。当用户要求更新 OpenClaw、同步源码、rebase 分支、或重新构建时触发。
---

# OpenClaw 源码更新

从源码更新 OpenClaw 到最新版本，同时保留本地修改。

## 工作流程

```bash
# 1. 进入项目目录
cd /home/ubuntu/projects/openclaw

# 2. 添加官方仓库（如果还没加）
git remote add upstream https://github.com/openclaw/openclaw.git 2>/dev/null || true

# 3. 获取官方更新
git fetch upstream

# 4. 更新 main 分支
git checkout main
git merge upstream/main

# 5. 查看完整更新内容（友好总结）
echo "=== 完整更新内容 ==="
# 获取当前和上一个版本的 tag
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v$(node -e 'console.log(require("./package.json").version)')
PREV_TAG=$(git tag --sort=-creatordate | grep -A1 "^$CURRENT_TAG$" | tail -n1
if [ "$PREV_TAG" = "$CURRENT_TAG" ]; then
  PREV_TAG=$(git tag --sort=-creatordate | grep -A2 "^$CURRENT_TAG$" | tail -n1)
fi

echo "当前版本: $CURRENT_TAG"
echo "上一版本: $PREV_TAG"
echo ""
echo "--- Git 提交记录 ---"
if [ -n "$PREV_TAG" ] && [ "$PREV_TAG" != "$CURRENT_TAG" ]; then
  git log "$PREV_TAG..HEAD" --oneline --no-decorate
else
  git log --oneline --no-decorate -50
fi
echo ""
echo "--- CHANGELOG 详细更新 ---"
# 找到 CHANGELOG 中当前版本的部分
if [ -f CHANGELOG.md ]; then
  CHANGELOG_CONTENT=$(awk '/^## [0-9]/{p=0} /^## '${CURRENT_TAG#v}'/{p=1} p' CHANGELOG.md)
  echo "$CHANGELOG_CONTENT"
  echo ""
  echo "--- 主要新增功能总结 ---"
  # 简单总结
  echo "$CHANGELOG_CONTENT" | awk '/^## /{p=0} /^### Changes/{p=1} p' | head -100 | sed 's/^- /*/'
fi

# 6. 切回功能分支并 rebase
git checkout feat/add-token-usage-to-agent-end-hook
git rebase main

# 7. 构建并安装
npm run build
npm i -g .

# 8. 检查版本
openclaw --version

# 9. 重启 gateway（可选）
systemctl --user restart openclaw-gateway
```

## 快捷脚本

执行 `scripts/update.sh` 自动完成以上所有步骤。

## 注意事项

- rebase 后如果推送到 fork，需要 `git push --force`
- 构建完成后需重启 gateway 才能生效
