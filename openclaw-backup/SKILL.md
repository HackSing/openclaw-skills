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

1. 在 GitHub 创建私人仓库（如 `openclaw-backup`）
2. 克隆到本地 Mac：
   ```bash
   git clone https://github.com/<你的用户名>/openclaw-backup.git
   ```
3. 每次备份后解压提交：
   ```bash
   cd openclaw-backup
   tar -xzf /tmp/openclaw-backup-20260216.tar.gz
   git add .
   git commit -m "Backup 2026-02-16"
   git push
   ```

## 恢复流程

参考：[迁移指南](https://docs.openclaw.ai/zh-CN/install/migrating)
