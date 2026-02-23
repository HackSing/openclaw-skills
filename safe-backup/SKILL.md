---
name: safe-backup
description: Backup OpenClaw state directory and workspace. Includes excluding sensitive files, packaging for backup. Triggered when user asks to backup, export, or save state.
---

# Safe Backup

Backup OpenClaw state directory and workspace with security best practices.

## ⚠️ Security Warnings

- **Backup may contain sensitive data** - review before sharing
- **If uploading to GitHub** - use a private repository and consider encryption
- **auth-profiles.json is EXCLUDED** - after restore, you must re-authenticate
- This script does NOT automatically push to any remote

## Quick Start

### 1. Run Backup

```bash
~/.openclaw/skills/safe-backup/scripts/backup.sh
```

### 2. Check Output

```
Backup file: /tmp/safe-backup-20260223.tar.gz
```

### 3. Store Securely

See "Storage Options" below.

---

## What Gets Backed Up

### ✅ Included (Safe to Backup)

| Directory | Contents |
|-----------|----------|
| `~/.openclaw/` | OpenClaw configuration |
| `~/.openclaw/workspace/` | Agent workspace files |
| `agents/` | Agent definitions |
| `skills/` | Installed skills |
| `memory/` | Memory files |
| `hooks/` | Custom hooks |

### ❌ Excluded (Sensitive - Not Backed Up)

| Pattern | Reason |
|---------|--------|
| `*.log` | Log files |
| `sessions.json` | Session data |
| `auth-profiles.json` | API tokens & credentials |
| `.env` | Environment variables |
| `*.pem`, `*.key` | TLS/SSH keys |
| `credentials.json` | Stored credentials |
| `api-keys.json` | API keys |

---

## Complete Workflow

### Phase 1: Backup

```bash
# Step 1: Run backup
~/.openclaw/skills/safe-backup/scripts/backup.sh

# Step 2: Verify backup contents
tar -tzf /tmp/safe-backup-20260223.tar.gz | less

# Step 3: Note the file path
# Output: /tmp/safe-backup-20260223.tar.gz
```

### Phase 2: Storage

Choose one:

#### Option A: Local Encrypted Storage (Recommended)

```bash
# Create encrypted archive
openssl enc -aes-256-cbc -salt -in /tmp/safe-backup-20260223.tar.gz -out ~/backups/safe-backup-20260223.tar.gz.enc

# Enter a strong password when prompted

# Delete unencrypted backup
rm /tmp/safe-backup-20260223.tar.gz
```

#### Option B: Private GitHub Repository

```bash
# One-time setup: Create private repo on GitHub

# Clone your private repo
git clone https://github.com/YOUR_USERNAME/safe-backup.git ~/safe-backup

# Extract backup
mkdir -p ~/safe-backup/2026-02-23
tar -xzf /tmp/safe-backup-20260223.tar.gz -C ~/safe-backup/2026-02-23/

# Commit and push
cd ~/safe-backup
git add .
git commit -m "Backup 2026-02-23"
git push origin main

# Delete local copy
rm -rf ~/safe-backup
rm /tmp/safe-backup-20260223.tar.gz
```

#### Option C: rsync to Remote Server

```bash
# Example: sync to remote server
rsync -avz --delete \
  --exclude='*.log' \
  --exclude='sessions.json' \
  ~/.openclaw/ user@backup-server:/path/to/backups/
```

### Phase 3: Restore

#### Step 1: Locate Backup

```bash
# If encrypted
openssl enc -aes-256-cbc -d -in ~/backups/safe-backup-20260223.tar.gz.enc -out /tmp/safe-backup.tar.gz

# If plain tarball
cp /path/to/safe-backup-20260223.tar.gz /tmp/
```

#### Step 2: Stop Gateway

```bash
systemctl --user stop openclaw-gateway
```

#### Step 3: Restore Files

```bash
# Extract to temporary location
mkdir -p /tmp/restore
tar -xzf /tmp/safe-backup.tar.gz -C /tmp/restore

# Restore state directory
cp -r /tmp/restore/state/* ~/.openclaw/

# Restore workspace (if needed)
cp -r /tmp/restore/workspace/* ~/.openclaw/workspace/
```

#### Step 4: Re-authenticate

Because `auth-profiles.json` was excluded, you must re-configure:

```bash
# Edit config to add authentication
openclaw config edit

# Or manually create auth-profiles.json
nano ~/.openclaw/agents/main/agent/auth-profiles.json
```

Required re-configuration:
- Telegram bot token
- Discord bot token  
- Feishu credentials
- Any other API keys

#### Step 5: Restart Gateway

```bash
systemctl --user start openclaw-gateway

# Verify
openclaw status
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENCLAW_STATE_DIR` | `$HOME/.openclaw` | OpenClaw state directory |
| `OPENCLAW_WORKSPACE_DIR` | `$HOME/.openclaw/workspace` | Workspace directory |

Example:

```bash
OPENCLAW_STATE_DIR=/data/openclaw ~/.openclaw/skills/safe-backup/scripts/backup.sh
```

---

## Troubleshooting

### "State directory not found"

```bash
# Check if OpenClaw is installed
ls -la ~/.openclaw
```

### "Permission denied"

```bash
# Run with appropriate permissions
chmod +x ~/.openclaw/skills/safe-backup/scripts/backup.sh
```

### Restore Fails

```bash
# Check backup integrity
tar -tzf /tmp/safe-backup.tar.gz

# If encrypted, verify password
openssl enc -aes-256-cbc -d -in backup.enc -o /dev/null
```

---

## Best Practices

1. **Backup regularly** - at least weekly
2. **Test restore** - periodically verify backups work
3. **Store offsite** - keep backup in different location
4. **Encrypt** - never store unencrypted backups in cloud
5. **Document** - keep notes on what was re-configured after restore
