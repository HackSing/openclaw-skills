---
name: safe-backup
description: Backup OpenClaw state directory and workspace. Includes excluding sensitive files, packaging for backup. Triggered when user asks to backup, export, or save state.
---

# Safe Backup

Backup OpenClaw state directory and workspace.

## ⚠️ Security Warnings

- **Backup may contain sensitive data** - review before sharing
- **If uploading to GitHub** - use a private repository and consider encryption
- This script does NOT automatically push to any remote

## Quick Backup

```bash
~/.openclaw/skills/safe-backup/scripts/backup.sh
```

Or with custom directories:

```bash
OPENCLAW_STATE_DIR=~/.openclaw OPENCLAW_WORKSPACE_DIR=~/.openclaw/workspace ~/.openclaw/skills/safe-backup/scripts/backup.sh
```

## Backup Contents

- `~/.openclaw/` (state directory)
- `~/.openclaw/workspace/` (workspace)

## Excluded Files (Sensitive)

- `*.log` - log files
- `*.log.*` - rotated logs
- `sessions.json` - session data
- `*.key`, `*.pem` - SSH/TLS keys
- `.env`, `.env.*` - environment files
- `id_rsa*`, `id_ed25519*` - SSH keys
- `*.secret`, `*.token` - secret files
- `auth-profiles.json` - authentication profiles (may contain tokens)
- `credentials.json` - credentials
- `api-keys.json` - API keys

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENCLAW_STATE_DIR` | `$HOME/.openclaw` | OpenClaw state directory |
| `OPENCLAW_WORKSPACE_DIR` | `$HOME/.openclaw/workspace` | Workspace directory |

## Manual Backup Flow

1. **Run backup script**:
   ```bash
   ~/.openclaw/skills/safe-backup/scripts/backup.sh
   ```
   Generates: `/tmp/safe-backup-YYYYMMDD.tar.gz`

2. **Review backup** (important!):
   ```bash
   tar -tzf /tmp/safe-backup-YYYYMMDD.tar.gz | less
   ```

3. **Store safely**:
   - Recommended: Encrypted storage (e.g., encrypted USB, password-protected archive)
   - If using GitHub: Use a **private** repository and consider git-crypt

## Restore Flow

Reference: [Migration Guide](https://docs.openclaw.ai/en-US/install/migrating)

## Security Recommendations

1. **Encrypt before uploading**:
   ```bash
   # Create encrypted archive
   tar -czf - backup-dir/ | openssl enc -aes-256-cbc -salt -out backup.tar.gz.enc
   # Decrypt
   openssl enc -aes-256-cbc -d -in backup.tar.gz.enc | tar -xzf -
   ```

2. **Use password manager** - never store backup passwords in the backup itself

3. **Verify exclusions** - regularly check what files are included in backups
