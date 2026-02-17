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

# 2. 更新 main 分支
git checkout main
git pull origin main

# 3. 切回功能分支并 rebase
git checkout feat/add-token-usage-to-agent-end-hook
git rebase main

# 4. 构建并安装
npm run build
npm i -g .

# 5. 重启 gateway
systemctl --user restart openclaw-gateway
```

## 快捷脚本

执行 `scripts/update.sh` 自动完成以上所有步骤。

## 注意事项

- rebase 后如果推送到 fork，需要 `git push --force`
- 构建完成后需重启 gateway 才能生效
