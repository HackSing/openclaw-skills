---
name: openclaw-backup
description: 备份 OpenClaw 状态目录和工作区。包括排除日志、会话等敏感文件，打包备份。当用户要求备份、导出、保存状态时触发。
---

# OpenClaw 备份

## 快速备份

```bash
/home/ubuntu/.openclaw/skills/openclaw-backup/scripts/backup.sh
```

## 备份内容

- `~/.openclaw/`（状态目录）
- `~/.openclaw/workspace/`（工作区）

## 排除的文件

- `*.log` 日志文件
- `sessions.json` 会话文件

## GitHub 备份流程

1. **初始化**（只需一次）：
   - 在 GitHub 创建私人仓库（如 `openclaw-backup`）
   - 克隆到本地：`git clone https://github.com/<你的用户名>/openclaw-backup.git`

2. **每次备份**：
   - 运行备份脚本，生成 `tar.gz` 文件（如 `/tmp/openclaw-backup-20260222.tar.gz`）
   - 解压覆盖到克隆目录：`tar -xzf /tmp/openclaw-backup-20260222.tar.gz -C /path/to/openclaw-backup`
   - 提交并推送：`cd /path/to/openclaw-backup && git add . && git commit -m "Backup 2026-02-22" && git push origin main`

**注意**：解压会覆盖旧文件，git 提交后 GitHub 上保存的就是最新备份。

## 恢复流程

参考：[迁移指南](https://docs.openclaw.ai/zh-CN/install/migrating)
